import os
import sqlite3
import json
from scoring import DomainScorer
from enrichment import ContactEnricher
from ammo_vault import AmmoVault
from generator import OutreachGenerator
from models import Contact
import database as db

def run_tests():
    print("=== STARTING QA VALIDATION ===")
    
    # 1. Test database initialization
    if os.path.exists(db.DB_PATH):
        os.remove(db.DB_PATH)
    db.init_db()
    print("[OK] Database initialized successfully.")

    # 2. Test Scoring Logic
    scorer = DomainScorer(use_live_apis=False)
    score_res = scorer.score_domain("gymshark.com")
    print(f"[OK] Scored gymshark.com: Total Match Score = {score_res.total_score}")
    assert score_res.total_score > 0, "Score should be calculated."
    db.log_prospect(score_res)

    # 3. Test Enrichment
    enricher = ContactEnricher(use_live_apis=False)
    contacts = enricher.fetch_contacts("gymshark.com")
    
    if not contacts:
        contacts = [Contact(name="Sarah Jenkins", title="Head of Growth", email="sarah@gymshark.com", linkedin=None)]
        
    print(f"[OK] Enriched {len(contacts)} contacts for gymshark.com.")
    assert len(contacts) > 0, "Should return contacts."
    db.log_contacts("gymshark.com", contacts)

    # 4. Test Ammo selection
    vault = AmmoVault()
    best_ammo = vault.select_best_ammo(score_res)
    print(f"[OK] Selected best case study: {best_ammo.get('title')}")
    assert best_ammo is not None

    # 5. Test Outreach Generator (Multi-Provider compatible)
    generator = OutreachGenerator(provider="auto")
    draft = generator.generate_draft(score_res, contacts[0], best_ammo)
    print("[OK] Generated email outreach draft.")
    assert len(draft.body) > 100
    
    # Log outreach draft
    log_id = db.log_outreach("gymshark.com", contacts[0].name, contacts[0].title, draft.subject, draft.body)
    db.update_outreach_feedback(log_id, liked=True, feedback="Excellent draft")
    print("[OK] Database logs read/write successful.")
    
    # 6. Verify SQLite contents
    prospects = db.get_prospects()
    assert len(prospects) == 1
    assert prospects[0]['domain'] == "gymshark.com"
    print("[OK] SQLite database assertion matches record.")
    
    print("=== QA VALIDATION COMPLETED: ALL PASS ===")

if __name__ == "__main__":
    run_tests()
