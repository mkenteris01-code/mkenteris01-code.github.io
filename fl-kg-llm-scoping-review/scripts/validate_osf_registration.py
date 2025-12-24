"""
OSF Registration PDF Validation Script
Checks for false claims, inconsistencies, and problematic language before submission
"""

import PyPDF2
import re
from pathlib import Path
from collections import defaultdict
import sys

# Fix Windows console encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

class OSFRegistrationValidator:
    def __init__(self, pdf_path):
        self.pdf_path = pdf_path
        self.issues = defaultdict(list)
        self.warnings = defaultdict(list)
        self.text = ""

    def extract_text(self):
        """Extract all text from PDF"""
        print(f"📄 Extracting text from: {self.pdf_path}")
        with open(self.pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            self.text = ""
            for page_num, page in enumerate(reader.pages, 1):
                self.text += f"\n--- PAGE {page_num} ---\n"
                self.text += page.extract_text()
        print(f"✅ Extracted {len(self.text)} characters from {len(reader.pages)} pages\n")

    def check_false_claims(self):
        """Check for PRIMARY false claims that must not appear"""
        print("🔍 Checking for FALSE CLAIMS (Critical Issues)...")

        false_claims = {
            "Zotero": [
                r"Zotero",
                r"zotero",
                r"reference management software",
                r"automated deduplication.*Zotero"
            ],
            "Rayyan": [
                r"Rayyan",
                r"rayyan",
                r"blind mode.*screening",
                r"blinded screening.*platform"
            ],
            "Systematic Review Claims": [
                r"systematic review.*PRISMA-P",
                r"prospective.*protocol",
                r"pre-registered.*search",
                r"benchmark validation procedure",
                r"gold standard.*validation"
            ],
            "Wrong Paper Count": [
                r"52\s+papers",
                r"52\s+core references",
                r"52\+",
                r"fifty-two papers"
            ],
            "Unpublished Manuscripts": [
                r"in press.*manuscripts.*included",
                r"in preparation.*manuscripts.*included",
                r"incorporates.*unpublished"
            ],
            "System Performance Claims": [
                r"proposed framework will achieve",
                r"system performance.*hypothesis",
                r"KGQI.*>.*0\.90",
                r"ACI.*>.*0\.90"
            ]
        }

        for category, patterns in false_claims.items():
            for pattern in patterns:
                matches = re.finditer(pattern, self.text, re.IGNORECASE)
                for match in matches:
                    # Get context (50 chars before and after)
                    start = max(0, match.start() - 50)
                    end = min(len(self.text), match.end() + 50)
                    context = self.text[start:end].replace('\n', ' ')
                    self.issues[category].append({
                        'match': match.group(),
                        'context': f"...{context}..."
                    })

        if any(self.issues.values()):
            print("❌ CRITICAL ISSUES FOUND:")
            for category, findings in self.issues.items():
                if findings:
                    print(f"\n  {category}: {len(findings)} instance(s)")
                    for i, finding in enumerate(findings[:3], 1):  # Show first 3
                        print(f"    {i}. '{finding['match']}'")
                        print(f"       Context: {finding['context']}")
        else:
            print("✅ No critical false claims found")

    def check_methodology_language(self):
        """Check for proper scoping review vs systematic review language"""
        print("\n🔍 Checking METHODOLOGY language...")

        # Should appear (good)
        good_terms = {
            "Scoping Review": r"scoping review",
            "PRISMA-ScR": r"PRISMA-ScR",
            "Retrospective Documentation": r"retrospective",
            "Exploratory": r"exploratory",
            "Iterative": r"iterative"
        }

        # Should NOT appear (bad)
        bad_terms = {
            "PRISMA-P (Systematic Protocol)": r"PRISMA-P",
            "Systematic Review (without scoping)": r"systematic review(?!.*scoping)",
            "Prospective Protocol": r"prospective.*protocol(?!.*future)",
            "Pre-registration (for search)": r"pre-registered.*search"
        }

        print("\n  Good Terms (Should Appear):")
        for term, pattern in good_terms.items():
            count = len(re.findall(pattern, self.text, re.IGNORECASE))
            status = "✅" if count > 0 else "⚠️"
            print(f"    {status} {term}: {count} occurrences")

        print("\n  Bad Terms (Should NOT Appear):")
        for term, pattern in bad_terms.items():
            matches = list(re.finditer(pattern, self.text, re.IGNORECASE))
            if matches:
                print(f"    ❌ {term}: {len(matches)} occurrences")
                for match in matches[:2]:
                    start = max(0, match.start() - 40)
                    end = min(len(self.text), match.end() + 40)
                    context = self.text[start:end].replace('\n', ' ')
                    self.warnings[term].append(f"...{context}...")
            else:
                print(f"    ✅ {term}: 0 occurrences")

    def check_consistency(self):
        """Check for internal consistency issues"""
        print("\n🔍 Checking CONSISTENCY...")

        # Extract all number mentions
        paper_counts = re.findall(r'(\d+)\s+papers?', self.text, re.IGNORECASE)
        unique_counts = set(paper_counts)

        print(f"\n  Paper counts mentioned: {unique_counts}")
        if '52' in unique_counts:
            print("  ❌ WARNING: '52 papers' found - should be 51!")
            self.warnings['Paper Count'].append("Found '52 papers' - should be 51")
        elif '51' in unique_counts and '52' not in unique_counts:
            print("  ✅ Paper count consistent (51)")

        # Check software mentions
        software_good = ["Python", "Qwen", "PyPDF2", "Pydantic"]
        software_bad = ["Zotero", "Rayyan", "EndNote"]

        print("\n  Software Mentions:")
        for sw in software_good:
            count = len(re.findall(sw, self.text, re.IGNORECASE))
            status = "✅" if count > 0 else "⚠️"
            print(f"    {status} {sw}: {count}")

        for sw in software_bad:
            count = len(re.findall(sw, self.text, re.IGNORECASE))
            if count > 0:
                print(f"    ❌ {sw}: {count} (SHOULD BE 0!)")
                self.issues['Bad Software'].append(sw)

    def check_timeline_clarity(self):
        """Check if timeline is clear (retrospective vs prospective)"""
        print("\n🔍 Checking TIMELINE clarity...")

        timeline_markers = {
            "Registration Date": r"December\s+23,?\s+2025",
            "Search Period": r"November.*December\s+2025",
            "Retrospective Label": r"RETROSPECTIVE",
            "Prospective Label": r"PROSPECTIVE",
            "Registration Point Marker": r"OSF REGISTRATION POINT"
        }

        for marker, pattern in timeline_markers.items():
            count = len(re.findall(pattern, self.text, re.IGNORECASE))
            status = "✅" if count > 0 else "⚠️"
            print(f"  {status} {marker}: {count} occurrences")
            if count == 0:
                self.warnings['Timeline'].append(f"Missing '{marker}'")

    def check_extraction_status(self):
        """Check that extraction status is correctly positioned"""
        print("\n🔍 Checking EXTRACTION STATUS...")

        # Bad: Extraction finished/completed
        bad_status = re.findall(r"extraction.*(?:finished|completed|done)", self.text, re.IGNORECASE)
        if bad_status:
            print(f"  ❌ Found 'Extraction Finished': {len(bad_status)} instances")
            print("     This contradicts 'registration before extraction' defense!")
            self.issues['Extraction Status'].extend(bad_status)
        else:
            print("  ✅ No 'extraction finished' claims")

        # Good: Extraction to be completed
        good_status = re.findall(r"extraction.*(?:to be completed|following registration)", self.text, re.IGNORECASE)
        if good_status:
            print(f"  ✅ Found correct status: {len(good_status)} instances")
        else:
            print("  ⚠️ Missing 'extraction to be completed' language")

    def generate_report(self):
        """Generate final validation report"""
        print("\n" + "="*70)
        print("📊 VALIDATION REPORT SUMMARY")
        print("="*70)

        total_issues = sum(len(v) for v in self.issues.values())
        total_warnings = sum(len(v) for v in self.warnings.values())

        print(f"\n🚨 CRITICAL ISSUES: {total_issues}")
        if total_issues > 0:
            print("\n⚠️  YOU MUST FIX THESE BEFORE SUBMISSION:")
            for category, findings in self.issues.items():
                if findings:
                    print(f"\n  [{category}] - {len(findings)} issue(s)")
                    for finding in findings:
                        if isinstance(finding, dict):
                            print(f"    • {finding['match']}")
                            print(f"      {finding['context']}")
                        else:
                            print(f"    • {finding}")
        else:
            print("  ✅ No critical issues - safe to submit!")

        print(f"\n⚠️  WARNINGS: {total_warnings}")
        if total_warnings > 0:
            print("\n  Review these (may be acceptable):")
            for category, findings in self.warnings.items():
                if findings:
                    print(f"\n  [{category}] - {len(findings)} warning(s)")
                    for warning in findings[:5]:  # Show first 5
                        print(f"    • {warning}")

        print("\n" + "="*70)
        if total_issues == 0 and total_warnings == 0:
            print("🎉 VALIDATION PASSED - Ready for OSF submission!")
        elif total_issues == 0:
            print("⚠️  No critical issues, but review warnings before submitting")
        else:
            print("❌ VALIDATION FAILED - Fix critical issues before submitting")
        print("="*70 + "\n")

        return total_issues, total_warnings

    def save_detailed_report(self, output_path):
        """Save detailed report to file"""
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("# OSF Registration Validation Report\n")
            f.write(f"**PDF:** {self.pdf_path}\n")
            f.write(f"**Date:** {Path(__file__).stat().st_mtime}\n\n")

            f.write("## Critical Issues\n\n")
            if self.issues:
                for category, findings in self.issues.items():
                    if findings:
                        f.write(f"### {category}\n\n")
                        for finding in findings:
                            if isinstance(finding, dict):
                                f.write(f"- **Match:** `{finding['match']}`\n")
                                f.write(f"  - Context: {finding['context']}\n")
                            else:
                                f.write(f"- {finding}\n")
                        f.write("\n")
            else:
                f.write("✅ No critical issues found.\n\n")

            f.write("## Warnings\n\n")
            if self.warnings:
                for category, findings in self.warnings.items():
                    if findings:
                        f.write(f"### {category}\n\n")
                        for warning in findings:
                            f.write(f"- {warning}\n")
                        f.write("\n")
            else:
                f.write("✅ No warnings.\n\n")

        print(f"💾 Detailed report saved to: {output_path}")

def main():
    import sys

    # Get PDF path from command line or use default
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
    else:
        pdf_path = r"C:\projects\AgenticAIpkg\docs\reports\osf screening\OSF_Registration_Final.pdf"

    print(f"🎯 Validating: {pdf_path}\n")

    if not Path(pdf_path).exists():
        print(f"❌ PDF not found: {pdf_path}")
        print("\nUsage: python validate_osf_registration.py [path_to_pdf]")
        return 1

    # Run validation
    validator = OSFRegistrationValidator(pdf_path)
    validator.extract_text()
    validator.check_false_claims()
    validator.check_methodology_language()
    validator.check_consistency()
    validator.check_timeline_clarity()
    validator.check_extraction_status()

    # Generate reports
    issues, warnings = validator.generate_report()

    # Save detailed report
    report_path = pdf_path.replace('.pdf', '_VALIDATION_REPORT.md')
    validator.save_detailed_report(report_path)

    # Return exit code
    return 0 if issues == 0 else 1

if __name__ == "__main__":
    exit(main())
