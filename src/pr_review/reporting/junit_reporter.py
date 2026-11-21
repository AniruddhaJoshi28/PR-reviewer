"""JUnit XML report generator for Jenkins test result archiving."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

from pr_review.models.base import ReviewReport, ScanStatus


class JUnitReporter:
    """Generates JUnit-compatible XML for Jenkins test reporting."""

    @staticmethod
    def generate_junit(report: ReviewReport, output_path: str | Path) -> str:
        testsuite = ET.Element(
            "testsuite",
            name="pr-review-pipeline",
            tests=str(len(report.scan_results) + 2),
            failures="0",
            errors="0",
            skipped="0",
        )

        failures_count = 0
        errors_count = 0
        skipped_count = 0

        # 1. SCM and Commit SHA verification testcase
        tc_scm = ET.SubElement(
            testsuite,
            "testcase",
            classname="pr_review.scm",
            name="verify_commit_metadata",
            time="0.05",
        )
        if not report.pr_metadata.head_sha or report.pr_metadata.head_sha.startswith("0000"):
            errors_count += 1
            err = ET.SubElement(tc_scm, "error", message="Invalid or zero commit SHA detected")
            err.text = f"HEAD SHA is invalid: {report.pr_metadata.head_sha}"

        # 2. Risk Classification testcase
        tc_risk = ET.SubElement(
            testsuite,
            "testcase",
            classname="pr_review.risk",
            name="deterministic_risk_classification",
            time="0.10",
        )
        # Always succeeds in executing classification

        # 3. Security scanners testcases
        for scan in report.scan_results:
            tc_scan = ET.SubElement(
                testsuite,
                "testcase",
                classname=f"pr_review.scanners.{scan.scanner_name}",
                name=f"security_scan_{scan.scanner_name}",
                time=str(scan.execution_time_seconds or 0.1),
            )
            if scan.status in (ScanStatus.FAIL, ScanStatus.MOCK_FAIL):
                failures_count += 1
                fail = ET.SubElement(tc_scan, "failure", message=f"{scan.scanner_name} detected findings")
                fail.text = f"Found {len(scan.findings)} security issues."
            elif scan.status == ScanStatus.ERROR:
                errors_count += 1
                err = ET.SubElement(tc_scan, "error", message=f"{scan.scanner_name} execution error")
                err.text = scan.error_message or "Unknown scanner error."
            elif scan.status == ScanStatus.NOT_RUN:
                skipped_count += 1
                ET.SubElement(tc_scan, "skipped", message=f"Scanner {scan.scanner_name} was NOT_RUN")

        testsuite.set("failures", str(failures_count))
        testsuite.set("errors", str(errors_count))
        testsuite.set("skipped", str(skipped_count))

        xml_str = ET.tostring(testsuite, encoding="utf-8", xml_declaration=True).decode("utf-8")
        out_p = Path(output_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        out_p.write_text(xml_str, encoding="utf-8")
        return xml_str
