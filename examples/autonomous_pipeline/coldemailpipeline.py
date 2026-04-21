import sys
import json
from typing import List, Optional
from pydantic import BaseModel, Field
from loguru import logger

from vessel.core.base import BaseVessel
from vessel.core.pipeline import VesselPipeline
from vessel.core.exceptions import CircuitBreakerTripped

# --- DATA MODELS ---

class Lead(BaseModel):
    name: str
    email: str
    company_context: str

class AnalyzedLead(BaseModel):
    lead: Lead
    pain_points: List[str]
    relevance_score: int

class DraftedEmail(BaseModel):
    recipient_email: str
    subject: str
    body: str

# --- SUB-VESSELS (The "Team") ---

class ScraperInput(BaseModel):
    niche: str
    limit: int

class ScraperOutput(BaseModel):
    leads: List[Lead]

class LeadScraperVessel(BaseVessel[ScraperInput, ScraperOutput]):
    """Scrapes raw leads from the web. Highly prone to rate limits (429s)."""
    def __init__(self):
        super().__init__()
        self._mock_attempts = 0

    def execute(self, inputs: ScraperInput) -> ScraperOutput:
        self._mock_attempts += 1
        logger.info(f"[LeadScraper] Attempt #{self._mock_attempts} to scrape {inputs.limit} leads for niche: {inputs.niche}")
        
        if self._mock_attempts < 3:
            logger.error("[LeadScraper] Hit 429 Too Many Requests from LinkedIn/Apollo.")
            raise ConnectionError("Rate limited by target API.")
            
        logger.success("[LeadScraper] Successfully bypassed rate limits and extracted leads.")
        return ScraperOutput(leads=[
            Lead(name="Alice", email="alpha@tech.io", company_context="Recent Series A, scaling engineering team."),
            Lead(name="Bob", email="bravo@cloud.net", company_context="Legacy infra, looking to modernize.")
        ][:inputs.limit])


class AnalyzerInput(BaseModel):
    leads: List[Lead]
    playbook_strategy: str

class AnalyzerOutput(BaseModel):
    analyzed_leads: List[AnalyzedLead]

class PlaybookAnalyzerVessel(BaseVessel[AnalyzerInput, AnalyzerOutput]):
    """Analyzes raw leads against the company playbook to find pain points."""
    def execute(self, inputs: AnalyzerInput) -> AnalyzerOutput:
        logger.info(f"[Analyzer] Analyzing {len(inputs.leads)} leads against playbook: {inputs.playbook_strategy}")
        results = []
        for lead in inputs.leads:
            # Simulated LLM analysis step (which might fail if the prompt is bad, but we handle it deterministically)
            if "scaling" in lead.company_context.lower():
                pain = "Hiring bottlenecks"
                score = 95
            else:
                pain = "Tech debt"
                score = 80
            results.append(AnalyzedLead(lead=lead, pain_points=[pain], relevance_score=score))
            
        logger.success(f"[Analyzer] Successfully scored {len(results)} leads.")
        return AnalyzerOutput(analyzed_leads=results)


class DrafterInput(BaseModel):
    analyzed_leads: List[AnalyzedLead]

class DrafterOutput(BaseModel):
    drafts: List[DraftedEmail]

class EmailDrafterVessel(BaseVessel[DrafterInput, DrafterOutput]):
    """Drafts personalized emails based on the analysis."""
    def execute(self, inputs: DrafterInput) -> DrafterOutput:
        logger.info(f"[Drafter] Drafting emails for {len(inputs.analyzed_leads)} high-value prospects.")
        drafts = []
        for a_lead in inputs.analyzed_leads:
            drafts.append(DraftedEmail(
                recipient_email=a_lead.lead.email,
                subject=f"Quick question about {a_lead.pain_points[0]} at {a_lead.lead.name}'s org",
                body=f"Hi {a_lead.lead.name},\n\nI noticed your company context: {a_lead.lead.company_context}. Let's chat.\n\nBest."
            ))
        logger.success(f"[Drafter] Created {len(drafts)} personalized drafts ready for review.")
        return DrafterOutput(drafts=drafts)


# --- THE MASTER PIPELINE ---

class ColdEmailPipelineInput(BaseModel):
    niche: str
    target_count: int
    playbook_context: str

class ColdEmailPipelineOutput(BaseModel):
    status: str
    final_drafts: List[DraftedEmail]

class ColdEmailPipeline(VesselPipeline[ColdEmailPipelineInput, ColdEmailPipelineOutput]):
    """
    Enterprise Pipeline: Scrape -> Analyze -> Draft.
    If ANY step fails catastrophically, the pipeline halts safely.
    If a step fails transiently (like the Scraper hitting 429s), it self-heals.
    """
    def __init__(self):
        super().__init__()
        # We instantiate our "Team"
        self.scraper = LeadScraperVessel()
        self.analyzer = PlaybookAnalyzerVessel()
        self.drafter = EmailDrafterVessel()

    def execute(self, inputs: ColdEmailPipelineInput) -> ColdEmailPipelineOutput:
        logger.info("=== STARTING COLD EMAIL PIPELINE ===")
        
        # Step 1: Scrape
        scrape_out = self.scraper.run({"niche": inputs.niche, "limit": inputs.target_count})
        
        if not scrape_out.leads:
            logger.warning("Pipeline halted: No leads found.")
            return ColdEmailPipelineOutput(status="No leads found", final_drafts=[])
            
        # Step 2: Analyze
        analysis_out = self.analyzer.run({
            "leads": [l.model_dump() for l in scrape_out.leads], 
            "playbook_strategy": inputs.playbook_context
        })
        
        # Filter only high relevance
        high_value = [al for al in analysis_out.analyzed_leads if al.relevance_score > 85]
        
        # Step 3: Draft
        draft_out = self.drafter.run({
            "analyzed_leads": [al.model_dump() for al in high_value]
        })
        
        logger.info("=== PIPELINE COMPLETED SUCCESSFULLY ===")
        return ColdEmailPipelineOutput(status="Success", final_drafts=draft_out.drafts)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: python {sys.argv[0]} '<json_payload>'", file=sys.stderr)
        sys.exit(1)
        
    try:
        payload = json.loads(sys.argv[1])
        pipeline = ColdEmailPipeline()
        result = pipeline.run(payload)
        print(result.model_dump_json(indent=2))
    except Exception as e:
        print(f"Fat Skill Execution Failed: {type(e).__name__} - {e}", file=sys.stderr)
        sys.exit(1)
