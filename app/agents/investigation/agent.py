import json
import logging
import re
from pathlib import Path
from typing import Any

from langchain_core.runnables import Runnable

from app.config.settings import settings
from app.core.incident_models import Incident
from app.llm.structured_output import InvestigationLLMOutput
from app.services.repository.local import LocalRepositoryProvider


logger = logging.getLogger(__name__)


class InvestigationAgent:
    def __init__(self, reasoning_chain: Runnable | None):
        self.reasoning_chain = reasoning_chain

    @staticmethod
    def _get_observation_text(incident: Incident) -> list[str]:
        observation = incident.observation
        texts: list[str] = []

        texts.extend(
            reason.message
            for reason in incident.trigger.reasons
            if reason.message
        )

        metrics = observation.get("metrics") if isinstance(observation, dict) else getattr(observation, "metrics", None)
        if metrics:
            texts.append(str(metrics))

        logs = observation.get("logs") if isinstance(observation, dict) else getattr(observation, "logs", [])
        if logs:
            texts.extend(getattr(log, "message", str(log)) for log in logs)

        exceptions = observation.get("exceptions") if isinstance(observation, dict) else getattr(observation, "exceptions", [])
        if exceptions:
            texts.extend(
                f"{exc.exception_type}: {exc.message}"
                if not isinstance(exc, str)
                else exc
                for exc in exceptions
            )

        traces = observation.get("traces") if isinstance(observation, dict) else getattr(observation, "traces", [])
        if traces:
            texts.extend(
                f"{trace.operation}: {trace.status}"
                if not isinstance(trace, str)
                else trace
                for trace in traces
            )

        return texts

    @staticmethod
    def _extract_code_clues(incident: Incident) -> list[str]:
        clues: list[str] = []
        for text in InvestigationAgent._get_observation_text(incident):
            if not text:
                continue
            clues.extend(InvestigationAgent._extract_route_clues(text))
            clues.extend(InvestigationAgent._extract_error_clues(text))

        unique: list[str] = []
        seen: set[str] = set()
        for clue in clues:
            key = clue.lower()
            if key not in seen and len(key) >= 3:
                seen.add(key)
                unique.append(clue)
        return unique[:30]

    @staticmethod
    def _extract_route_clues(text: str) -> list[str]:
        clues: list[str] = []
        for route in re.findall(r"/[A-Za-z0-9_./-]{3,}", text):
            normalized_route = route.rstrip(".,:;)")
            clues.append(normalized_route)
            parts = [part for part in normalized_route.split("/") if part]
            if len(parts) > 1:
                clues.append("/".join(parts[-2:]))
            if parts:
                clues.append(parts[-1])
        return clues

    @staticmethod
    def _extract_runtime_routes(incident: Incident) -> list[str]:
        runtime_text = " ".join(
            InvestigationAgent._get_observation_text(incident)
        )
        routes = [
            route.rstrip(".,:;)")
            for route in re.findall(r"/[A-Za-z0-9_./{}:-]{3,}", runtime_text)
        ]
        return list(dict.fromkeys(routes))

    @staticmethod
    def _extract_runtime_errors(incident: Incident) -> list[str]:
        runtime_text = " ".join(
            InvestigationAgent._get_observation_text(incident)
        )
        errors = re.findall(
            r"\b[A-Z][A-Za-z0-9]*(?:Error|Exception|Failure|NotFound)\b",
            runtime_text,
        )
        status_codes = re.findall(r"\b(?:HTTP\s*)?([45]\d{2})\b", runtime_text, re.IGNORECASE)
        return list(dict.fromkeys(errors + [f"HTTP {code}" for code in status_codes]))

    @staticmethod
    def _extract_error_clues(text: str) -> list[str]:
        ignored = {
            "error", "request", "service", "trace", "api", "requests",
            "response", "status", "object", "bool", "int", "str",
            "float", "dict", "list", "type", "returned", "http",
        }
        clues: list[str] = []
        for token in re.findall(r"[A-Za-z][A-Za-z0-9_./-]{2,}", text):
            lowered = token.lower()
            if "__" in lowered or lowered.startswith("main") or lowered in ignored:
                continue
            if (
                token[0].isupper()
                or "_" in token
                or "." in token
                or lowered in {"workflow", "router", "route", "endpoint"}
                or any(word in lowered for word in ("timeout", "exception", "notfound"))
            ):
                clues.append(token)
        return clues

    @staticmethod
    def _empty_repository_result(reason: str | None = None) -> dict[str, Any]:
        result = {
            "code_evidence": [],
            "code_findings": [],
            "code_change_suggestions": [],
        }
        if reason:
            result["code_findings"] = [{
                "file": None,
                "line": None,
                "lines": None,
                "symbol": None,
                "issue": reason,
                "evidence": None,
                "confidence": 0.0,
            }]
        return result

    def investigate_repository(
        self,
        incident: Incident,
        repository: str | Path | LocalRepositoryProvider | None = None,
    ) -> dict[str, Any]:
        if repository is None:
            repository_path = settings.repository_path            
            if repository_path is None or not str(repository_path).strip():
                return self._empty_repository_result(
                    "Repository analysis unavailable because no repository path is configured."
                )
            try:
                repository = LocalRepositoryProvider(
                    repository_path,
                    ignored_dirs=set(settings.repository_ignored_dirs),
                    max_file_size_kb=settings.repository_max_file_size_kb,
                    max_files=settings.repository_max_files,
                    max_search_results=settings.repository_max_search_results,
                )
            except ValueError as exc:
                logger.warning("[Repository] Unavailable: %s", exc)
                return self._empty_repository_result(
                    f"Repository analysis unavailable because the configured repository could not be accessed: {exc}"
                )

        if isinstance(repository, (str, Path)):
            repository_path = str(repository).strip()
            if not repository_path:
                return self._empty_repository_result(
                    "Repository analysis unavailable because the repository path is empty."
                )
            try:
                repository = LocalRepositoryProvider(
                    repository,
                    ignored_dirs=set(settings.repository_ignored_dirs),
                    max_file_size_kb=settings.repository_max_file_size_kb,
                    max_files=settings.repository_max_files,
                    max_search_results=settings.repository_max_search_results,
                )
            except ValueError as exc:
                logger.warning("[Repository] Unavailable: %s", exc)
                return self._empty_repository_result(
                    f"Repository analysis unavailable because the configured repository could not be accessed: {exc}"
                )

        clues = self._extract_code_clues(incident)
        if not clues:
            return self._empty_repository_result(
                "No relevant source-code search clues were found in the incident."
            )

        checked_files = [
            file_name
            for file_name in repository.list_files(
                max_files=settings.repository_max_files,
            )
            if Path(file_name).suffix
        ]
        logger.info(
            "[Repository] Investigation checking %d files",
            len(checked_files),
        )
        for file_name in checked_files:
            logger.info("[Repository] Checked file: %s", file_name)

        all_search_results: list[dict[str, Any]] = []
        for clue in clues:
            try:
                matches = repository.search(clue, max_results=10, context_lines=2)
            except (ValueError, OSError, RuntimeError) as exc:
                logger.warning("[Repository] Search failed for %s: %s", clue, exc)
                continue
            all_search_results.extend(matches)

        all_search_results = self._rank_search_results(
            all_search_results,
            incident,
        )

        all_search_results = self._select_actionable_results(
            all_search_results,
            incident,
        )

        logger.info(
            "[Repository] Actionable matches: %s",
            ", ".join(
                dict.fromkeys(match["file"] for match in all_search_results)
            ) or "none",
        )

        if not all_search_results:
            return self._empty_repository_result(
                "No relevant source-code references were found in the configured repository."
            )

        code_evidence: list[dict[str, Any]] = []
        code_findings: list[dict[str, Any]] = []
        suggestion_candidates: list[dict[str, Any]] = []

        seen_files: set[str] = set()
        for match in all_search_results[:8]:
            file_name = match["file"]
            if file_name in seen_files:
                continue
            seen_files.add(file_name)
            try:
                match_line = int(match["line"])
                read_result = repository.read_file(
                    file_name,
                    start_line=max(1, match_line - 12),
                    end_line=match_line + 18,
                    max_lines=40,
                )
            except (FileNotFoundError, ValueError) as exc:
                logger.warning("[Repository] Read failed for %s: %s", file_name, exc)
                continue
            letter_match = match["match"]
            symbol = re.search(r"(?:def|class)\s+([A-Za-z_]\w*)", read_result["snippet"])
            symbol_name = symbol.group(1) if symbol else self._extract_route_symbol(letter_match, file_name)
            reason = f"Repository search found {letter_match} in {file_name} within {symbol_name}, which matches the observed exception or service clue."
            code_evidence.append(
                {
                    "file": file_name,
                    "start_line": read_result["start_line"],
                    "end_line": read_result["end_line"],
                    "lines": f"{read_result['start_line']}-{read_result['end_line']}",
                    "snippet": read_result["snippet"],
                    "relevance": "high",
                    "reason": reason,
                }
            )
            code_findings.append(
                {
                    "file": file_name,
                    "line": match["line"],
                    "lines": str(match["line"]),
                    "symbol": symbol_name,
                    "issue": self._build_finding_issue(
                        incident,
                        letter_match,
                        all_search_results,
                    ),
                    "evidence": match["match"],
                    "confidence": self._finding_confidence(match),
                }
            )
            suggestion_candidates.append(
                {
                    "file": file_name,
                    "line": match["line"],
                    "lines": str(match["line"]),
                    "symbol": symbol_name,
                    "problem": f"Observed runtime clue {letter_match} appears in this code path.",
                    "suggestion": self._build_change_suggestion(
                        incident,
                        read_result["snippet"],
                        letter_match,
                        all_search_results,
                    ),
                    "change": self._build_change_suggestion(
                        incident,
                        read_result["snippet"],
                        letter_match,
                        all_search_results,
                    ),
                    "priority": "high" if "404" in " ".join(InvestigationAgent._get_observation_text(incident)) else "medium",
                    "reason": reason,
                    "confidence": self._finding_confidence(match),
                }
            )

        if not suggestion_candidates:
            suggestion_candidates = [{
                "file": all_search_results[0]["file"],
                "line": all_search_results[0]["line"],
                "lines": str(all_search_results[0]["line"]),
                "symbol": all_search_results[0]["file"],
                "problem": "Runtime evidence aligns with a repository code path.",
                "suggestion": "Inspect the surrounding implementation and align it with the observed runtime failure.",
                "change": "Inspect the surrounding implementation and align it with the observed runtime failure.",
                "priority": "medium",
                "reason": "Observed runtime clues were found in repository code.",
                "confidence": 0.7,
            }]

        return {
            "code_evidence": code_evidence,
            "code_findings": code_findings,
            "code_change_suggestions": suggestion_candidates,
        }

    @staticmethod
    def _rank_search_results(
        matches: list[dict[str, Any]],
        incident: Incident,
    ) -> list[dict[str, Any]]:
        runtime_text = " ".join(
            InvestigationAgent._get_observation_text(incident)
        ).lower()
        requested_route = next(
            iter(InvestigationAgent._extract_route_clues(runtime_text)),
            "",
        )
        unique: dict[tuple[str, int], dict[str, Any]] = {}
        for match in matches:
            key = (match["file"], match["line"])
            score = 0
            file_name = match["file"].lower()
            content = match["match"].lower()
            if requested_route and requested_route in content:
                score += 100
            if re.search(r"@(app|router)\.(get|post|put|patch|delete)|add_api_route|route\(", content):
                score += 80
            if any(part in file_name for part in ("api", "router", "route", "main", "server", "controller")):
                score += 30
            if any(part in file_name for part in ("inspect", "debug", "test", "wave", "example")):
                score -= 40
            if content.startswith(("#", "print(")):
                score -= 25
            candidate = dict(match)
            candidate["_score"] = score
            unique[key] = max(unique.get(key, candidate), candidate, key=lambda item: item["_score"])
        return sorted(unique.values(), key=lambda item: item["_score"], reverse=True)

    @staticmethod
    def _is_source_file(file_name: str) -> bool:
        return Path(file_name).suffix.lower() in {
            ".c", ".cc", ".cpp", ".cs", ".go", ".java", ".js", ".jsx",
            ".php", ".py", ".rb", ".rs", ".ts", ".tsx", ".vue",
        }

    @staticmethod
    def _is_route_registration(match: dict[str, Any]) -> bool:
        return bool(
            re.search(
                r"@(app|router)\.(get|post|put|patch|delete)|"
                r"add_api_route|routes?\.(add|append)|app\.(get|post|put|patch|delete)",
                f"{match.get('match', '')}\n{match.get('context', '')}",
                re.IGNORECASE,
            )
        )

    @classmethod
    def _select_actionable_results(
        cls,
        matches: list[dict[str, Any]],
        incident: Incident,
    ) -> list[dict[str, Any]]:
        """Keep repository context focused on files that can be changed."""
        source_matches = [
            match for match in matches if cls._is_source_file(match["file"])
        ]
        runtime_routes = cls._extract_runtime_routes(incident)
        if not runtime_routes:
            return source_matches[:8]

        route_matches = [
            match for match in source_matches
            if cls._is_route_registration(match)
        ]
        if route_matches:
            return route_matches[:3]
        return source_matches[:8]

    @staticmethod
    def _extract_route_symbol(match: str, file_name: str) -> str:
        route_match = re.search(r"(?:get|post|put|patch|delete)\s*\([^)]*['\"]([^'\"]+)", match, re.IGNORECASE)
        return route_match.group(1) if route_match else file_name

    @staticmethod
    def _finding_confidence(match: dict[str, Any]) -> float:
        score = match.get("_score", 0)
        return min(0.95, max(0.55, 0.65 + max(score, 0) / 400))

    @staticmethod
    def _build_finding_issue(
        incident: Incident,
        match: str,
        search_results: list[dict[str, Any]],
    ) -> str:
        runtime_routes = InvestigationAgent._extract_runtime_routes(incident)
        repository_routes = InvestigationAgent._find_route_literals(search_results)
        if runtime_routes and repository_routes:
            routes = InvestigationAgent._find_route_literals(search_results)
            if routes:
                return (
                    f"The runtime referenced {', '.join(runtime_routes[:3])}, while "
                    f"repository route evidence includes {', '.join(routes[:5])}. "
                    "Compare the caller and registered route before concluding "
                    "there is a route mismatch."
                )
        errors = InvestigationAgent._extract_runtime_errors(incident)
        error_context = f" for {', '.join(errors[:3])}" if errors else ""
        return f"Repository evidence related to '{match}'{error_context} may be involved in the incident."

    @staticmethod
    def _build_change_suggestion(
        incident: Incident,
        snippet: str,
        match: str,
        search_results: list[dict[str, Any]],
    ) -> str:
        runtime_routes = InvestigationAgent._extract_runtime_routes(incident)
        repository_routes = InvestigationAgent._find_route_literals(search_results)
        if runtime_routes and repository_routes:
            return (
                "Compare the runtime route(s) "
                f"{', '.join(runtime_routes[:3])} with repository route definitions "
                f"{', '.join(repository_routes[:5])}. Update the caller or route "
                "registration so the contract matches, then verify the service "
                "configuration and port."
            )
        errors = InvestigationAgent._extract_runtime_errors(incident)
        error_context = ", ".join(errors[:3]) or "the observed runtime failure"
        return (
            f"Inspect the surrounding implementation for {error_context} and update "
            f"the code around '{match}' to handle the observed failure while "
            "preserving the existing runtime contract."
        )

    @staticmethod
    def _find_route_literals(matches: list[dict[str, Any]]) -> list[str]:
        routes: list[str] = []
        for match in matches:
            if not re.search(r"route|router|api|main|server", match["file"], re.IGNORECASE):
                continue
            routes.extend(re.findall(r"['\"](/[A-Za-z0-9_./{}:-]+)['\"]", match["match"]))
        return list(dict.fromkeys(routes))

    def build_code_change_suggestion(self, repository_result: dict[str, Any]) -> dict[str, Any]:
        suggestions = repository_result.get("code_change_suggestions") or []
        if not suggestions:
            code_findings = repository_result.get("code_findings") or []
            if not code_findings:
                return {}
            suggestion = {
                "file": code_findings[0]["file"],
                "line": code_findings[0]["line"],
                "symbol": code_findings[0].get("symbol", "unknown"),
                "problem": code_findings[0]["issue"],
                "suggestion": "Add targeted timeout, backoff, or error handling to the relevant code path and validate with a focused regression test.",
                "reason": "The code path matches the incident runtime evidence.",
                "confidence": code_findings[0].get("confidence", 0.75),
            }
            return suggestion
        return suggestions[0]

    @staticmethod
    def prepare_context(
        incident: Incident,
        evidence: list[Any],
        observation: Any,
        repository_context: dict[str, Any] | None = None,
    ) -> dict[str, str]:
        incident_context = {
            "incident_id": incident.incident_id,
            "project_id": incident.project_id,
            "service": incident.service,
            "severity": incident.severity.value,
            "status": incident.status.value,
            "detection_reasons": [
                reason.model_dump(mode="json")
                for reason in incident.trigger.reasons
            ],
        }
        if hasattr(observation, "model_dump"):
            observation_context = observation.model_dump(mode="json")
        else:
            observation_context = observation
        repository_payload = repository_context or {
            "repository_path": None,
            "code_evidence": [],
            "code_findings": [],
            "code_change_suggestions": [],
        }
        return {
            "incident_context": json.dumps(incident_context, indent=2),
            "evidence_context": json.dumps(observation_context, indent=2, default=str),
            "repository_context": json.dumps(repository_payload, indent=2),
        }

    async def investigate(
        self,
        context: dict[str, str],
    ) -> InvestigationLLMOutput:

        if self.reasoning_chain is None:
            return InvestigationLLMOutput(
                correlations=[],
                timeline=[],
                affected_dependencies=[],
                summary="Investigation completed using runtime and repository evidence without LLM synthesis.",
                uncertainties=["LLM unavailable; evidence was assembled from structured runtime and repository output."],
                code_evidence=[],
                code_findings=[],
                code_change_suggestions=[],
            )

        logger.info("[LLM] Investigation reasoning started")

        output = await self.reasoning_chain.ainvoke(context)

        result = InvestigationLLMOutput.model_validate(output)

        logger.info("[LLM] Investigation reasoning completed")

        return result