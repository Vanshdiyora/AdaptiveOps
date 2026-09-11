import argparse
import asyncio
import logging

from app.agents.observation.agent import ObservationAgent
from app.core.exceptions import LLMConfigurationError, InvestigationWorkflowError
from app.services.incident_service import IncidentService
from app.services.investigation_service import InvestigationService


def build_parser() -> argparse.ArgumentParser:
	parser = argparse.ArgumentParser(
		description="Run AdaptiveOps agent workflows."
	)
	parser.set_defaults(
		command="investigation",
		project_id="Investment Research Agent",
		service="investment-research-agent",
		minutes=10,
	)
	subparsers = parser.add_subparsers(dest="command")

	for command, help_text in (
		("observation", "Collect and display service telemetry."),
		(
			"investigation",
			"Observe a service, detect an incident, and investigate it.",
		),
	):
		command_parser = subparsers.add_parser(command, help=help_text)
		command_parser.add_argument(
			"--project-id",
			default="demo-commerce",
			help="Project identifier (default: %(default)s).",
		)
		command_parser.add_argument(
			"--service",
			default="order-service",
			help="Service name (default: %(default)s).",
		)
		command_parser.add_argument(
			"--minutes",
			type=int,
			default=10,
			help="Observation window in minutes (default: %(default)s).",
		)

	return parser


def print_observation(observation) -> None:
	print("\n" + "=" * 60)
	print("ADAPTIVEOPS OBSERVATION")
	print("=" * 60)
	print(f"Project: {observation.project_id}")
	print(f"Service: {observation.service}")
	print(f"Health: {observation.health_status}")

	print("\n--- Metrics ---")
	print(f"Requests: {observation.metrics.request_count}")
	print(f"Errors: {observation.metrics.error_count}")
	print(f"Error Rate: {observation.metrics.error_rate}%")
	print(f"P50 Latency: {observation.metrics.latency_p50_ms} ms")
	print(f"P95 Latency: {observation.metrics.latency_p95_ms} ms")

	print("\n--- Logs ---")
	for log in observation.logs:
		print(f"[{log.level}] {log.message}")

	print("\n--- Traces ---")
	for trace in observation.traces:
		print(f"{trace.operation} {trace.duration_ms}ms {trace.status}")

	print("\n--- Exceptions ---")
	for exception in observation.exceptions:
		print(f"{exception.exception_type}: {exception.message}")


def print_detection(incident) -> None:
	print("\n" + "=" * 60)
	print("ADAPTIVEOPS DETECTION")
	print("=" * 60)
	print(f"Incident ID: {incident.incident_id}")
	print(f"Severity: {incident.severity.value}")
	print(f"Status: {incident.status.value}")

	print("\n--- Detection Reasons ---")
	for reason in incident.trigger.reasons:
		print(f"[{reason.severity.value}] {reason.message}")


def print_repository_analysis(investigation) -> None:
	print("\n--- Repository Code Findings ---")
	print(f"Repository: {investigation.repository_path or 'Not configured'}")
	if investigation.code_findings:
		for finding in investigation.code_findings:
			print(f"\nFile: {finding.get('file', 'Unknown')}")
			print(f"Line: {finding.get('line', 'Unknown')}")
			print(f"Symbol: {finding.get('symbol', 'Unknown')}")
			print(f"Issue: {finding.get('issue', 'Unknown')}")
			print(f"Evidence: {finding.get('evidence', 'Unknown')}")
			print(f"Confidence: {finding.get('confidence', 0):.2f}")
	else:
		print("- No matching repository code was found")

	print("\n--- Required Code Changes ---")
	if investigation.code_change_suggestions:
		for suggestion in investigation.code_change_suggestions:
			print(f"\nFile: {suggestion.get('file', 'Unknown')}")
			print(f"Line: {suggestion.get('line', 'Unknown')}")
			print(f"Symbol: {suggestion.get('symbol', 'Unknown')}")
			print(f"Problem: {suggestion.get('problem', 'Unknown')}")
			print(f"Change: {suggestion.get('suggestion', 'Unknown')}")
			print(f"Reason: {suggestion.get('reason', 'Unknown')}")
			print(f"Confidence: {suggestion.get('confidence', 0):.2f}")
	else:
		print("- No code change suggestions were generated")


def print_investigation(investigation) -> None:
	print("\n" + "=" * 60)
	print("ADAPTIVEOPS INVESTIGATION")
	print("=" * 60)
	print(f"Incident: {investigation.incident_id}")
	print(f"Service: {investigation.service}")

	print("\n--- Evidence ---")
	for evidence in investigation.evidence:
		print(f"\n[{evidence.type.value}] {evidence.signal}")
		print(f"Value: {evidence.value}")
		print(f"Description: {evidence.description}")

	print("\n--- Correlations ---")
	for correlation in investigation.correlations:
		print(
			f"\n{correlation.source_evidence_id}"
			f" -> {correlation.target_evidence_id}"
		)
		print(f"Relationship: {correlation.relationship}")
		print(f"Confidence: {correlation.confidence:.2f}")

	print("\n--- Timeline ---")
	for event in investigation.timeline:
		print(f"\n[{event.event_type}]")
		print(event.description)

	print("\n--- Affected Dependencies ---")
	if investigation.affected_dependencies:
		for dependency in investigation.affected_dependencies:
			print(f"- {dependency}")
	else:
		print("- None identified")

	print("\n--- Investigation Summary ---")
	print(investigation.summary)

	print("\n--- Uncertainties ---")
	if investigation.uncertainties:
		for uncertainty in investigation.uncertainties:
			print(f"- {uncertainty}")
	else:
		print("- None reported")

	print_repository_analysis(investigation)


async def main() -> None:
	args = build_parser().parse_args()

	observation = await ObservationAgent().run(
		project_id=args.project_id,
		service=args.service,
		minutes=args.minutes,
	)
	print_observation(observation)

	if args.command == "observation":
		return

	incident = IncidentService().detect(observation)
	if incident is None:
		print("\nNo incident detected.")
		return

	print_detection(incident)
	try:
		investigation = await InvestigationService().investigate(incident)
	except (LLMConfigurationError, InvestigationWorkflowError) as error:
		print("\n" + "=" * 60)
		print("ADAPTIVEOPS INVESTIGATION")
		print("=" * 60)
		print("Status: FAILED")
		print(f"Error: {error}")
		return

	print_investigation(investigation)


if __name__ == "__main__":
	logging.basicConfig(level=logging.INFO, format="%(message)s")
	asyncio.run(main())
