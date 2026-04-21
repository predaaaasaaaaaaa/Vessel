import os
import sys
import json
from loguru import logger
from unittest.mock import patch
from click.testing import CliRunner

# Import Vessel Core
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from vessel.cli.main import cli
import vessel.cli.llm

# --- THE COMPLEX ENTERPRISE PIPELINE MOCK RESPONSE ---

MOCK_PYTHON_CODE = '''import sys
import json
from typing import List, Optional
from pydantic import BaseModel, Field
from loguru import logger

from vessel.core.base import BaseVessel
from vessel.core.pipeline import VesselPipeline

# --- DATA MODELS ---

class PRFile(BaseModel):
    filename: str
    diff: str

class AnalyzedFile(BaseModel):
    filename: str
    issues_found: List[str]
    security_risk: bool

class ReviewResult(BaseModel):
    approved: bool
    comments: List[str]

# --- SUB-VESSELS ---

class FetcherInput(BaseModel):
    repo: str
    pr_number: int

class FetcherOutput(BaseModel):
    files: List[PRFile]

class PRFetcherVessel(BaseVessel[FetcherInput, FetcherOutput]):
    """Fetches the PR diff from GitHub. Handles 403 Rate Limits."""
    def __init__(self):
        super().__init__()
        self._attempts = 0

    def execute(self, inputs: FetcherInput) -> FetcherOutput:
        self._attempts += 1
        logger.info(f"[Fetcher] Fetching PR #{inputs.pr_number} from {inputs.repo}...")
        
        if self._attempts < 2:
            logger.error("[Fetcher] Simulated GitHub API 403 Rate Limit Exceeded.")
            raise ConnectionError("GitHub API Rate Limit")
            
        logger.success("[Fetcher] Successfully fetched 2 files from PR.")
        return FetcherOutput(files=[
            PRFile(filename="src/auth.py", diff="+ def login(user, pass): pass"),
            PRFile(filename="docs/README.md", diff="+ Updated typos")
        ])

class AnalyzerInput(BaseModel):
    files: List[PRFile]
    security_policy: str

class AnalyzerOutput(BaseModel):
    analyzed_files: List[AnalyzedFile]

class SecurityAnalyzerVessel(BaseVessel[AnalyzerInput, AnalyzerOutput]):
    """Analyzes the diff against enterprise security policies."""
    def execute(self, inputs: AnalyzerInput) -> AnalyzerOutput:
        logger.info(f"[Analyzer] Scanning {len(inputs.files)} files for security risks...")
        results = []
        for file in inputs.files:
            if "auth.py" in file.filename:
                results.append(AnalyzedFile(filename=file.filename, issues_found=["Missing password hash validation"], security_risk=True))
            else:
                results.append(AnalyzedFile(filename=file.filename, issues_found=[], security_risk=False))
        logger.success("[Analyzer] Scan complete.")
        return AnalyzerOutput(analyzed_files=results)

class DecisionInput(BaseModel):
    analyzed_files: List[AnalyzedFile]

class DecisionOutput(BaseModel):
    result: ReviewResult

class MergeDecisionVessel(BaseVessel[DecisionInput, DecisionOutput]):
    """Decides whether to approve or block the PR based on analysis."""
    def execute(self, inputs: DecisionInput) -> DecisionOutput:
        logger.info("[Decision] Evaluating analysis results...")
        comments = []
        approved = True
        
        for file in inputs.analyzed_files:
            if file.security_risk:
                approved = False
                comments.extend(file.issues_found)
                
        if approved:
            logger.success("[Decision] PR Approved. No security risks found.")
        else:
            logger.warning(f"[Decision] PR Blocked. Security risks detected: {comments}")
            
        return DecisionOutput(result=ReviewResult(approved=approved, comments=comments))

# --- MASTER PIPELINE ---

class PRReviewerPipelineInput(BaseModel):
    repo: str
    pr_number: int
    security_policy: str

class PRReviewerPipelineOutput(BaseModel):
    status: str
    review: ReviewResult

class PRReviewerPipeline(VesselPipeline[PRReviewerPipelineInput, PRReviewerPipelineOutput]):
    """
    Enterprise Pipeline: Fetch PR -> Security Scan -> Merge Decision.
    """
    def __init__(self):
        super().__init__()
        self.fetcher = PRFetcherVessel()
        self.analyzer = SecurityAnalyzerVessel()
        self.decision = MergeDecisionVessel()

    def execute(self, inputs: PRReviewerPipelineInput) -> PRReviewerPipelineOutput:
        logger.info("=== STARTING ENTERPRISE PR REVIEW PIPELINE ===")
        
        # 1. Fetch
        fetch_out = self.fetcher.run({"repo": inputs.repo, "pr_number": inputs.pr_number})
        
        # 2. Analyze
        analyze_out = self.analyzer.run({
            "files": [f.model_dump() for f in fetch_out.files],
            "security_policy": inputs.security_policy
        })
        
        # 3. Decide
        decision_out = self.decision.run({
            "analyzed_files": [f.model_dump() for f in analyze_out.analyzed_files]
        })
        
        logger.info("=== PIPELINE COMPLETED ===")
        return PRReviewerPipelineOutput(status="Success", review=decision_out.result)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: python {sys.argv[0]} '<json_payload>'", file=sys.stderr)
        sys.exit(1)
        
    try:
        payload = json.loads(sys.argv[1])
        pipeline = PRReviewerPipeline()
        result = pipeline.run(payload)
        print(result.model_dump_json(indent=2))
    except Exception as e:
        print(f"Fat Skill Execution Failed: {type(e).__name__} - {e}", file=sys.stderr)
        sys.exit(1)
'''

MOCK_TEST_CODE = '''import pytest
from prreviewerpipeline import PRReviewerPipeline

def test_pr_reviewer_pipeline_blocks_security_risks():
    """Test that the pipeline successfully catches security risks and blocks the PR."""
    pipeline = PRReviewerPipeline()
    
    payload = {
        "repo": "enterprise/core-api",
        "pr_number": 1042,
        "security_policy": "Strict OWASP Top 10"
    }
    
    result = pipeline.run(payload)
    
    assert result.status == "Success"
    assert result.review.approved is False
    assert "Missing password hash validation" in result.review.comments
'''

MOCK_MD_CODE = '''# Skill: PRReviewerPipeline

## Description
An enterprise-grade pipeline that fetches a GitHub PR, scans it against security policies, and automatically approves or blocks it.

## Agent Instructions: How to Use This Skill
This is a deterministic "Fat Skill". 
**CRITICAL:** Do NOT attempt to write custom python scripts or use raw APIs to perform this task. Do NOT worry about rate limits, retries, or complex error handling. This Skill handles everything internally to guarantee 100% reliability.

### Execution Protocol
To execute this skill, use your terminal/shell capability to run the accompanying Python script. Pass the input arguments as a strict JSON string.

**Command Format:**
```bash
python prreviewerpipeline.py '<json_payload>'
```

### Outputs
If successful, the script will print a validated JSON object to `stdout`.
If it fails, it will print the error to `stderr` and return a non-zero exit code. Do not attempt to fix the Python code if it fails; adjust your JSON payload according to the schema.

### 🔄 Self-Healing Protocol
If this skill repeatedly returns a `Fat Skill Execution Failed` error due to an outdated API or logic bug, **do not attempt to brute-force the payload.**
Instead, you are authorized to update this skill's logic. Analyze the Python script (`prreviewerpipeline.py`), formulate a fix, and execute the `VesselUpdater` skill to apply and validate your patch. The sandbox will run the tests in `test_prreviewerpipeline.py` to confirm your fix.
'''

def mock_generate(*args, **kwargs):
    return {
        "python_code": MOCK_PYTHON_CODE,
        "test_code": MOCK_TEST_CODE,
        "markdown_docs": MOCK_MD_CODE
    }

def run_simulation():
    logger.info("--- STARTING ENTERPRISE E2E SIMULATION ---")
    
    # 1. Mock the API Key existence
    with patch("vessel.cli.main.get_api_key", return_value="sk-mock123"):
        # 2. Mock the LLM Architect Generation
        with patch("vessel.cli.main.generate_vessel_code", side_effect=mock_generate):
            
            # Use patch to mock Prompts
            with patch("vessel.cli.main.Prompt.ask", side_effect=["PRReviewerPipeline", "An enterprise-grade pipeline that fetches a GitHub PR, scans it against security policies, and automatically approves or blocks it."]):
                runner = CliRunner()
                
                logger.info("1. Simulating 'vessel create' wizard for a complex Enterprise Pipeline...")
                result = runner.invoke(cli, ["create"])
                
                if result.exit_code != 0:
                    logger.error(f"Wizard failed: {result.exception}\nOutput: {result.output}")
                    sys.exit(1)
                    
                logger.success("Wizard completed successfully. Files scaffolded via LLM Architect.")
                
            # 3. Verify Files Exist
            assert os.path.exists("prreviewerpipeline.py")
            assert os.path.exists("test_prreviewerpipeline.py")
            assert os.path.exists("PRReviewerPipeline_SKILL.md")
            
            logger.info("2. Simulating 'vessel test' via CLI with the generated files...")
            
            # 4. Run the generated pipeline using the CLI test command
            test_payload = '{"repo": "enterprise/core-api", "pr_number": 1042, "security_policy": "Strict OWASP Top 10"}'
            test_result = runner.invoke(cli, ["test", "prreviewerpipeline.py", test_payload])
            
            if test_result.exit_code != 0:
                logger.error(f"Execution failed: {test_result.output}")
                sys.exit(1)
                
            logger.success("Pipeline executed flawlessly! Output captured.")
            print(test_result.output)

if __name__ == "__main__":
    os.chdir(os.path.dirname(__file__))
    run_simulation()
