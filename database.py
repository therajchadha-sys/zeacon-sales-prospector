import sqlite3
import json
import os
from typing import List, Dict, Any, Optional
from models import DomainScore, Contact

DB_PATH = 'zeacon_prospector.db'

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA journal_mode=WAL;")
    except Exception:
        pass
    return conn

def init_db():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS prospects (
                domain TEXT PRIMARY KEY,
                video_ads_score INTEGER,
                traffic_score INTEGER,
                onsite_video_score INTEGER,
                cart_score INTEGER,
                total_score INTEGER,
                details TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS brand_telemetry (
                domain TEXT PRIMARY KEY,
                traffic_tier TEXT,
                traffic_score INTEGER,
                source TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                domain TEXT,
                name TEXT,
                title TEXT,
                email TEXT,
                linkedin TEXT,
                FOREIGN KEY(domain) REFERENCES prospects(domain) ON DELETE CASCADE
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS outreach_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                domain TEXT,
                contact_name TEXT,
                persona TEXT,
                subject TEXT,
                body TEXT,
                liked INTEGER DEFAULT 0,
                feedback TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS strategy_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                domain TEXT,
                strategy_angle TEXT,
                liked INTEGER DEFAULT 0,
                critique TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS client_feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                domain TEXT,
                category TEXT,
                rating TEXT,
                feedback TEXT,
                submitted_by TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        # Winning Outreach Templates / Examples Vault table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS winning_outreach (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                email_body TEXT,
                notes TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS case_studies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT UNIQUE,
                metric TEXT,
                focus TEXT,
                description TEXT
            )
        ''')
        conn.commit()

        # Seed with Kris's real-world proven case studies and winning email templates
        cursor.execute('SELECT COUNT(*) as count FROM case_studies')
        if cursor.fetchone()['count'] <= 5:
            kris_studies = [
                ('Nettlebrook Table 30-Day Controlled Split Test', '+66% Online Order Lift (+56% Reservations)', 'A/B Controlled Split Test', 
                 'In a 30-day controlled split test across 13,847 sessions, Zeacon video widgets generated +66% more online orders, +56% more table reservations, +55% phone calls, and +47% catering form fills compared to the control group. Video watchers logged 14.2 page interactions vs 6.5 control.'),
                ('Quantum Energy Squares D2C Lift', '8% to 12% Online Sales Lift', 'Social Content Personalization', 
                 'Quantum Energy Squares integrated Zeacon to repurpose their existing Instagram, Facebook, and YouTube video libraries into personalized website feeds, driving an 8-12% increase in online checkout conversions.'),
                ('Behind-the-Scenes & Chef Spotlight Video Study', '11.01% Conversion vs 4.42% Control', 'Trust-Building Video Content', 
                 'Behind-the-scenes kitchen tours and chef spotlight videos converted at 10.63% to 11.01% (nearly 3x higher than static control pages), demonstrating that authentic team video builds maximum buyer trust.'),
                ('Logarithmic Dwell-Time Conversion Model', 'CR = α * ln(TOS) + β', 'Empirical Conversion Science', 
                 'Research across Wyzowl, Animoto, and CXL Institute confirms 82% of consumers are convinced to buy after watching brand videos. Time-on-site (TOS) scales conversion probability logarithmically, raising the conversion curve without hard-selling.'),
                ('Aston Martin Bellevue Luxury Lead Engine', 'High-Ticket Engagement Lift', 'Automotive Video Experiences', 
                 'Aston Martin of Bellevue utilizes Zeacon interactive video players to showcase luxury vehicles directly to high-intent buyers, personalizing the dealership experience.'),
                ('Minamoto Japanese Cuisine Booking Boost', 'Elevated Booking Conversion', 'Hospitality & Dining Widgets', 
                 'Minamoto Cuisine uses Zeacon technology to display seasonal omakase and dining video feeds, significantly accelerating online reservation checkouts.')
            ]
            for s in kris_studies:
                cursor.execute('''
                    INSERT OR REPLACE INTO case_studies (title, metric, focus, description)
                    VALUES (?, ?, ?, ?)
                ''', s)
            conn.commit()

        # Seed winning outreach templates with Kris's example
        cursor.execute('SELECT COUNT(*) as count FROM winning_outreach')
        if cursor.fetchone()['count'] == 0:
            kris_winning_template = (
                "Hi [Name], Zeacon's been helping brands increase sales by personalizing content for every viewer that enters your website. "
                "The personalization comes from content that is already in your content library (Instagram, Facebook, and YouTube). "
                "Our current customers see an 8% to 12% increase in online sales. It's extremely cost effective and helps engage customers to make buying decisions. "
                "We can also inform which paid ads are most effective for conversion on the website, helping lower your customer acquisition cost (CAC)."
            )
            cursor.execute('''
                INSERT INTO winning_outreach (title, email_body, notes)
                VALUES (?, ?, ?)
            ''', ('Kris Real Closed Deal Email', kris_winning_template, 'Proven formula highlighting IG/FB/YouTube video library reuse, 8-12% sales lift, and CAC reduction.'))
            conn.commit()

def log_prospect(score: DomainScore):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO prospects (domain, video_ads_score, traffic_score, onsite_video_score, cart_score, total_score, details)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            score.domain,
            score.video_ads_score,
            score.traffic_score,
            score.onsite_video_score,
            score.cart_score,
            score.total_score,
            json.dumps(score.details)
        ))
        conn.commit()

def log_contacts(domain: str, contacts: List[Contact]):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM contacts WHERE domain = ?', (domain,))
        for c in contacts:
            cursor.execute('''
                INSERT INTO contacts (domain, name, title, email, linkedin)
                VALUES (?, ?, ?, ?, ?)
            ''', (domain, c.name, c.title, c.email, c.linkedin))
        conn.commit()

def log_outreach(domain: str, contact_name: str, persona: str, subject: str, body: str):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO outreach_logs (domain, contact_name, persona, subject, body)
            VALUES (?, ?, ?, ?, ?)
        ''', (domain, contact_name, persona, subject, body))
        conn.commit()
        return cursor.lastrowid

def update_outreach_feedback(log_id: int, liked: bool, feedback: str = ''):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE outreach_logs
            SET liked = ?, feedback = ?
            WHERE id = ?
        ''', (1 if liked else 0, feedback, log_id))
        conn.commit()

def log_strategy_feedback(domain: str, strategy_angle: str, liked: bool, critique: str = ''):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO strategy_logs (domain, strategy_angle, liked, critique)
            VALUES (?, ?, ?, ?)
        ''', (domain, strategy_angle, 1 if liked else 0, critique))
        conn.commit()

def add_winning_outreach(title: str, email_body: str, notes: str = ''):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO winning_outreach (title, email_body, notes)
            VALUES (?, ?, ?)
        ''', (title, email_body, notes))
        conn.commit()

def get_winning_outreach() -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM winning_outreach ORDER BY timestamp DESC')
        rows = cursor.fetchall()
        return [dict(r) for r in rows]

def get_prospects() -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM prospects ORDER BY timestamp DESC')
        rows = cursor.fetchall()
        return [dict(r) for r in rows]

def get_contacts_for_domain(domain: str) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM contacts WHERE domain = ?', (domain,))
        rows = cursor.fetchall()
        return [dict(r) for r in rows]

def get_outreach_logs() -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM outreach_logs ORDER BY timestamp DESC')
        rows = cursor.fetchall()
        return [dict(r) for r in rows]

def get_strategy_logs() -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM strategy_logs ORDER BY timestamp DESC')
        rows = cursor.fetchall()
        return [dict(r) for r in rows]

def get_case_studies() -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM case_studies')
        rows = cursor.fetchall()
        return [dict(r) for r in rows]

def add_case_study(title: str, metric: str, focus: str, description: str):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO case_studies (title, metric, focus, description)
            VALUES (?, ?, ?, ?)
        ''', (title, metric, focus, description))
        conn.commit()

def get_brand_telemetry(domain: str) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT *, datetime(timestamp, '+30 days') > datetime('now') as is_fresh FROM brand_telemetry WHERE domain = ?", (domain.lower(),))
        row = cursor.fetchone()
        if row and row['is_fresh']:
            return dict(row)
        return None

def save_brand_telemetry(domain: str, traffic_tier: str, traffic_score: int, source: str = "ai_learned"):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO brand_telemetry (domain, traffic_tier, traffic_score, source)
            VALUES (?, ?, ?, ?)
        ''', (domain.lower(), traffic_tier, traffic_score, source))
        conn.commit()

def log_client_feedback(domain: str, category: str, rating: str, feedback: str, submitted_by: str = "Kris / Client"):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO client_feedback (domain, category, rating, feedback, submitted_by)
            VALUES (?, ?, ?, ?, ?)
        ''', (domain, category, rating, feedback, submitted_by))
        conn.commit()

def get_client_feedback() -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM client_feedback ORDER BY timestamp DESC')
        rows = cursor.fetchall()
        return [dict(r) for r in rows]
