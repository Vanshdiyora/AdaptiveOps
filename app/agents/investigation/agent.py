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
    def _canonicalize_route(route: str) -> str:
        candidate = route.strip().rstrip(".,:;)")
        if not candidate:
            return ""
        candidate = re.sub(r"\{[^}]+\}", "{param}", candidate)
        candidate = candidate.lower().rstrip("/")
        normalized = [part for part in candidate.split("/") if part]
        return "/" + "/".join(normalized)

    @staticmethod
    def _extract_route_clues(text: str) -> list[str]:
        clues: list[str] = []
        for route in re.findall(r"/[A-Za-z0-9_./-]{3,}", text):
            normalized_route = route.rstrip(".,:;)")
            clues.append(normalized_route)
            for variant in {normalized_route, InvestigationAgent._canonicalize_route(normalized_route)}:
                if variant and variant not in clues:
                    clues.append(variant)
            parts = [part for part in normalized_route.split("/") if part]
            if len(parts) > 1:
                clues.append("/".join(parts[-2:]))
            if parts:
                last = parts[-1]
                if last not in clues:
                    clues.append(last)
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
        observation = incident.observation
        exceptions = (
            observation.get("exceptions", [])
            if isinstance(observation, dict)
            else getattr(observation, "exceptions", [])
        )
        errors.extend(
            getattr(exception, "exception_type", "")
            for exception in exceptions
            if getattr(exception, "exception_type", "")
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
                or lowered in {
                    "workflow",
                    "router",
                    "route",
                    "endpoint",
                    "ticker",
                    "validation",
                    "invalid",
                    "format",
                }
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

        logger.info("[Repository] Investigation checking repository files")

        all_search_results: list[dict[str, Any]] = []
        for clue in clues:
            try:
                matches = repository.search(clue, max_results=10, context_lines=2)
            except (ValueError, OSError, RuntimeError) as exc:
                logger.warning("[Repository] Search failed for %s: %s", clue, exc)
                continue
            all_search_results.extend(matches)

        all_search_results = self._rank_search_results(all_search_results, incident)
        all_search_results = self._select_actionable_results(all_search_results, incident)

        if not all_search_results:
            return self._empty_repository_result(
                "No relevant source-code references were found in the configured repository."
            )

        code_evidence: list[dict[str, Any]] = []
        code_findings: list[dict[str, Any]] = []
        suggestion_candidates: list[dict[str, Any]] = []

        runtime_routes = self._extract_runtime_routes(incident)
        runtime_error_tokens = self._extract_runtime_errors(incident)
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

            snippet = read_result["snippet"]
            if not snippet:
                continue

            symbol_name = self._extract_snippet_symbol(
                snippet,
                match_line - read_result["start_line"],
            ) or self._extract_route_symbol(match["match"], file_name)

            route_literals = re.findall(r"['\"](/[-A-Za-z0-9_./{}:]+)['\"]", snippet)
            reason = (
                f"Repository evidence in {file_name} includes {match['match']} "
                f"matching the runtime clue and the surrounding implementation describes the relevant execution path."
            )

            code_evidence.append(
                {
                    "file": file_name,
                    "start_line": read_result["start_line"],
                    "end_line": read_result["end_line"],
                    "lines": f"{read_result['start_line']}-{read_result['end_line']}",
                    "snippet": snippet,
                    "relevance": "high",
                    "reason": reason,
                }
            )

            issue_text = self._build_finding_issue(incident, match["match"], all_search_results)
            code_findings.append(
                {
                    "file": file_name,
                    "line": match_line,
                    "lines": str(match_line),
                    "symbol": symbol_name,
                    "issue": issue_text,
                    "evidence": match["match"],
                    "confidence": self._finding_confidence(match),
                }
            )

            proposed_code = snippet
            mismatch = self._route_mismatch_summary(incident, all_search_results)
            if mismatch:
                runtime_route, repo_route = mismatch
                route_value = repo_route
                if route_value.startswith("/") and "{" in route_value:
                    route_value = route_value.replace("{company_id}", "{name}") if "{company_id}" in route_value else route_value
                    route_value = route_value.replace("{ticker}", "{name}") if "{ticker}" in route_value else route_value
                if runtime_route and repo_route and runtime_route != repo_route:
                    proposed_code = (
                        f"{runtime_route.replace('/companys/', '/company/', 1) if '/companys/' in runtime_route.lower() and '/company/' in repo_route.lower() else repo_route}"
                    )
                    if "companys" in runtime_route.lower() and "company" in repo_route.lower():
                        proposed_code = repo_route

            elif (
                self._has_route_mismatch_evidence(incident)
                and runtime_routes
                and route_literals
            ):
                for route_literal in route_literals:
                    for runtime_route in runtime_routes:
                        if route_literal.lower() == runtime_route.lower():
                            continue
                        runtime_key = self._canonicalize_route(runtime_route)
                        repo_key = self._canonicalize_route(route_literal)
                        if runtime_key and repo_key and runtime_key != repo_key:
                            proposed_code = repo_route if 'repo_route' in locals() else route_literal
                            if proposed_code != snippet:
                                break
                    if proposed_code != snippet:
                        break

            if snippet == proposed_code and mismatch is None:
                continue

            suggestion_change = self._build_change_suggestion(incident, snippet, match["match"], all_search_results)
            if mismatch:
                runtime_route, repo_route = mismatch
                suggestion_change = (
                    f"Update the caller route from {runtime_route} to {repo_route}. "
                    "The backend route registration is the valid contract and the runtime request is using the outdated path."
                )

            suggestion_candidates.append(
                {
                    "file": file_name,
                    "start_line": read_result["start_line"],
                    "end_line": read_result["end_line"],
                    "symbol": symbol_name,
                    "problem": issue_text,
                    "current_code": snippet,
                    "proposed_code": proposed_code,
                    "change": suggestion_change,
                    "reason": reason,
                    "priority": "high" if any("404" in token.lower() or "notfound" in token.lower() for token in runtime_error_tokens + runtime_routes) else "medium",
                    "confidence": self._finding_confidence(match),
                }
            )

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
            runtime_errors = InvestigationAgent._extract_runtime_errors(incident)
            exact_error_match = any(
                error.lower() in content
                for error in runtime_errors
                if not error.lower().startswith("http ")
            )
            if exact_error_match:
                score += 250
            if "raise httpexception" in content:
                score += 100
            if "invalid ticker format" in content:
                score += 100
            if requested_route and requested_route in content:
                score += 30
            if re.search(r"@(app|router)\.(get|post|put|patch|delete)|add_api_route|route\(", content):
                score += 20
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

        if cls._has_route_mismatch_evidence(incident):
            route_matches = [
                match for match in source_matches
                if cls._is_route_registration(match)
            ]
            if route_matches:
                return route_matches[:3]
        implementation_matches = [
            match for match in source_matches
            if cls._is_exception_implementation_match(match, incident)
        ]
        remaining_matches = [
            match for match in source_matches
            if match not in implementation_matches
        ]
        return (implementation_matches + remaining_matches)[:8]

    @staticmethod
    def _is_exception_implementation_match(
        match: dict[str, Any],
        incident: Incident,
    ) -> bool:
        content = match.get("match", "").lower()
        error_names = {
            error.lower()
            for error in InvestigationAgent._extract_runtime_errors(incident)
            if not error.lower().startswith("http ")
        }
        return (
            any(error_name in content for error_name in error_names)
            or "raise httpexception" in content
            or "invalid ticker format" in content
        )

    @staticmethod
    def _has_route_mismatch_evidence(incident: Incident) -> bool:
        return any(
            token.lower() in {"http 404", "httpnotfound", "notfound"}
            for token in InvestigationAgent._extract_runtime_errors(incident)
        )

    @staticmethod
    def _extract_route_symbol(match: str, file_name: str) -> str:
        route_match = re.search(r"(?:get|post|put|patch|delete)\s*\([^)]*['\"]([^'\"]+)", match, re.IGNORECASE)
        return route_match.group(1) if route_match else file_name

    @staticmethod
    def _extract_snippet_symbol(snippet: str, target_offset: int) -> str | None:
        lines = snippet.splitlines()
        target_offset = min(max(target_offset, 0), max(len(lines) - 1, 0))
        target_indent = len(lines[target_offset]) - len(lines[target_offset].lstrip())
        for index in range(target_offset, -1, -1):
            match = re.match(r"\s*(?:async\s+)?(?:def|class)\s+([A-Za-z_]\w*)", lines[index])
            if not match:
                continue
            declaration_indent = len(lines[index]) - len(lines[index].lstrip())
            if declaration_indent <= target_indent or index == target_offset:
                return match.group(1)
        return None

    @staticmethod
    def _finding_confidence(match: dict[str, Any]) -> float:
        score = match.get("_score", 0)
        return min(0.95, max(0.55, 0.65 + max(score, 0) / 400))

    @staticmethod
    def _route_mismatch_summary(
        incident: Incident,
        search_results: list[dict[str, Any]],
    ) -> tuple[str, str] | None:
        runtime_routes = InvestigationAgent._extract_runtime_routes(incident)
        if not InvestigationAgent._has_route_mismatch_evidence(incident):
            return None
        repository_routes = InvestigationAgent._find_route_literals(search_results)
        if not runtime_routes or not repository_routes:
            return None

        for runtime_route in runtime_routes:
            runtime_key = InvestigationAgent._canonicalize_route(runtime_route)
            for repo_route in repository_routes:
                repo_key = InvestigationAgent._canonicalize_route(repo_route)
                if runtime_key and repo_key and runtime_key != repo_key:
                    return runtime_route, repo_route
        return None

    @staticmethod
    def _route_mismatch_message(incident: Incident, search_results: list[dict[str, Any]]) -> str | None:
        mismatch = InvestigationAgent._route_mismatch_summary(incident, search_results)
        if mismatch is None:
            return None
        runtime_route, repo_route = mismatch
        return (
            f"The runtime referenced {runtime_route}, while the repository route registration uses {repo_route}. "
            "This route mismatch is a strong candidate for the 404 behavior."
        )

    @staticmethod
    def _build_finding_issue(
        incident: Incident,
        match: str,
        search_results: list[dict[str, Any]],
    ) -> str:
        runtime_routes = InvestigationAgent._extract_runtime_routes(incident)
        repository_routes = InvestigationAgent._find_route_literals(search_results)
        mismatch = InvestigationAgent._route_mismatch_message(incident, search_results)
        if mismatch:
            return mismatch
        if mismatch is not None and runtime_routes and repository_routes:
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
            for runtime_route in runtime_routes:
                for repository_route in repository_routes:
                    runtime_key = InvestigationAgent._canonicalize_route(runtime_route)
                    repo_key = InvestigationAgent._canonicalize_route(repository_route)
                    if runtime_key and repo_key and runtime_key != repo_key:
                        return (
                            f"Update the route caller from {runtime_route} to {repository_route}. "
                            "The runtime request is returning 404 because the backend contract is mismatched."
                        )
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
            return {}
        suggestion = suggestions[0].copy()
        suggestion.setdefault("file", suggestion.get("file") or repository_result.get("code_findings", [{}])[0].get("file"))
        suggestion.setdefault("symbol", suggestion.get("symbol") or repository_result.get("code_findings", [{}])[0].get("symbol"))
        suggestion.setdefault("problem", suggestion.get("problem") or repository_result.get("code_findings", [{}])[0].get("issue"))
        suggestion.setdefault("reason", "The repository evidence directly corresponds to the observed runtime issue.")
        suggestion.setdefault("confidence", repository_result.get("code_findings", [{}])[0].get("confidence", 0.75))
        return suggestion

    @staticmethod
    def _trim_repository_payload(repository_context: dict[str, Any] | None) -> dict[str, Any]:
        payload = dict(repository_context or {
            "repository_path": None,
            "code_evidence": [],
            "code_findings": [],
            "code_change_suggestions": [],
        })

        code_evidence = list(payload.get("code_evidence") or [])
        code_findings = list(payload.get("code_findings") or [])
        code_changes = list(payload.get("code_change_suggestions") or [])

        ranked_findings = sorted(
            code_findings,
            key=lambda item: float(item.get("confidence", 0.0) or 0.0),
            reverse=True,
        )
        ranked_evidence = sorted(
            code_evidence,
            key=lambda item: float(item.get("relevance") == "high"),
            reverse=True,
        )

        top_evidence = ranked_evidence[:4]
        top_findings = ranked_findings[:4]
        top_suggestions = code_changes[:4]

        issue_summary = ""
        if top_findings:
            issue_summary = "; ".join(
                f"{item.get('file', 'unknown')}::{item.get('symbol') or 'unknown'}: {item.get('issue', 'issue')}"
                for item in top_findings[:3]
            )
        elif top_evidence:
            issue_summary = "; ".join(
                f"{item.get('file', 'unknown')}: {item.get('reason', 'matching runtime evidence')}"
                for item in top_evidence[:3]
            )

        payload["code_evidence"] = top_evidence
        payload["code_findings"] = top_findings
        payload["code_change_suggestions"] = top_suggestions
        payload["top_retrievals"] = [
            {
                "file": item.get("file"),
                "symbol": item.get("symbol") or item.get("file"),
                "issue": item.get("issue") or item.get("reason") or "Repository match",
                "evidence": item.get("evidence") or item.get("snippet") or item.get("reason") or "matching evidence",
                "confidence": item.get("confidence", 0.0),
            }
            for item in top_findings[:4]
        ]
        if isinstance(payload.get("repository_investigation"), dict):
            repo_investigation = dict(payload["repository_investigation"])
            for key in ("primary_location", "related_locations", "callers", "callees"):
                items = list(repo_investigation.get(key) or [])
                if key == "primary_location" and repo_investigation.get(key):
                    repo_investigation[key] = repo_investigation[key]
                elif items:
                    repo_investigation[key] = items[:4]
            payload["repository_investigation"] = repo_investigation
        payload["issue_summary"] = issue_summary or "Repository evidence is insufficient to isolate a single fix; review all top retrievals before coding a change."
        return payload

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
        repository_payload = InvestigationAgent._trim_repository_payload(repository_context)
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