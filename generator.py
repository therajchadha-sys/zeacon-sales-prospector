import os
import requests
import json
import urllib.parse
import re
import random
from bs4 import BeautifulSoup
from typing import Dict, Any, Optional
from models import OutreachDraft, DomainScore, Contact
import database as db

try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False

try:
    from google import genai
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False


class OutreachGenerator:
    def __init__(self, provider: str = "auto", anthropic_api_key: Optional[str] = None, gemini_api_key: Optional[str] = None):
        self.provider = provider
        self.anthropic_key = anthropic_api_key or os.getenv("ANTHROPIC_API_KEY")
        self.gemini_key = gemini_api_key or os.getenv("GEMINI_API_KEY")
        
        self.ollama_url = "http://localhost:11434/api/generate"
        self.local_model_name = "llama3.2:latest"
        
        self.playbook = self._load_playbook()
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'
        ]

    def _load_playbook(self) -> dict:
        try:
            with open('sales_playbook.json', 'r') as f:
                return json.load(f)
        except Exception:
            return {}

    def _scrape_brand_news(self, domain: str) -> str:
        clean_brand = domain.split('.')[0]
        query = f"{clean_brand} news OR announcement OR solutions"
        headers = {
            'User-Agent': random.choice(self.user_agents)
        }
        try:
            encoded_query = urllib.parse.quote_plus(query)
            url = f"https://html.duckduckgo.com/html/?q={encoded_query}"
            resp = requests.get(url, headers=headers, timeout=6)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                snippets = soup.find_all('a', class_='result__snippet')
                text_snippets = [s.get_text().strip() for s in snippets[:3]]
                if text_snippets:
                    return " | ".join(text_snippets)
        except Exception:
            pass
        return "Expanding service capabilities and scaling digital customer acquisition channels."

    def _query_claude(self, system_prompt: str, user_prompt: str) -> str:
        if not HAS_ANTHROPIC or not self.anthropic_key:
            return ""
        try:
            client = anthropic.Anthropic(api_key=self.anthropic_key)
            message = client.messages.create(
                model="claude-3-5-sonnet-latest",
                max_tokens=300,
                temperature=0.3,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}]
            )
            text_blocks = [b.text for b in message.content if hasattr(b, 'text') and b.text]
            if text_blocks:
                return text_blocks[-1].strip()
        except Exception as e:
            print(f"Claude API Error: {e}")
            return ""

    def _query_gemini(self, system_prompt: str, user_prompt: str) -> str:
        if not HAS_GEMINI or not self.gemini_key:
            return ""
        try:
            client = genai.Client(api_key=self.gemini_key)
            full_prompt = f"{system_prompt}\n\nUSER REQUEST:\n{user_prompt}"
            response = client.models.generate_content(
                model="gemini-flash-latest",
                contents=full_prompt
            )
            return response.text.strip()
        except Exception as e:
            print(f"Gemini API Error: {e}")
            return ""

    def _query_local_llm(self, prompt: str) -> str:
        try:
            payload = {
                "model": self.local_model_name,
                "prompt": prompt,
                "stream": False,
                "raw": True,
                "options": {
                    "num_predict": 250,
                    "temperature": 0.25,
                    "top_p": 0.9,
                    "stop": ["Subject:", "Hi ", "Hello ", "\n\n\n"]
                }
            }
            resp = requests.post(self.ollama_url, json=payload, timeout=15)
            if resp.status_code == 200:
                return resp.json().get("response", "").strip()
        except Exception:
            pass
        return ""

    def _compile_historical_feedback(self) -> str:
        logs = db.get_outreach_logs()
        strat_logs = db.get_strategy_logs()
        winning_templates = db.get_winning_outreach()
        
        positive_lessons = []
        negative_lessons = []
        
        for l in logs:
            fb = l.get('feedback', '')
            liked = l.get('liked')
            if fb:
                if liked == 1:
                    positive_lessons.append(f"Email: {fb}")
                elif liked == 0:
                    negative_lessons.append(f"Email: {fb}")
                    
        for s in strat_logs:
            fb = s.get('critique', '')
            liked = s.get('liked')
            if fb:
                if liked == 1:
                    positive_lessons.append(f"Strategy Tactic: {fb}")
                elif liked == 0:
                    negative_lessons.append(f"Strategy Tactic: {fb}")
                    
        feedback_context = ""
        if winning_templates:
            feedback_context += "\nPROVEN PROSE & WINNING TEMPLATES (KRIS'S REAL CLOSED DEALS):\n"
            for w in winning_templates[:2]:
                feedback_context += f"- Style Pattern '{w.get('title')}': \"{w.get('email_body')}\"\n"

        if positive_lessons:
            feedback_context += "\nPAST CRITIQUE - CRITICAL ALIGNMENT RULES (WHAT WORKED):\n"
            for p in set(positive_lessons[:4]):
                feedback_context += f"- Follow this rule: {p}\n"
        if negative_lessons:
            feedback_context += "\nPAST CRITIQUE - CRITICAL ALIGNMENT RULES (WHAT TO AVOID/FIX):\n"
            for n in set(negative_lessons[:4]):
                feedback_context += f"- Avoid doing this: {n}\n"
                
        return feedback_context

    def generate_draft(self, domain_score: DomainScore, contact: Contact, case_study: Dict[str, Any], user_tweak: str = "") -> OutreachDraft:
        clean_domain = domain_score.domain.split('.')[0].capitalize()
        if clean_domain.lower() == 'roberthalf':
            clean_domain = "Robert Half"
            
        brand_news = self._scrape_brand_news(domain_score.domain)
        
        business_type = domain_score.details.get('business_type', 'Commercial Enterprise')
        conversion_model = domain_score.details.get('conversion_model', 'Digital Conversion Engine')
        social_platforms = domain_score.details.get('social_active_platforms', '')
        social_correlation = domain_score.details.get('social_correlation', '')

        title_lower = contact.title.lower()
        strategy = {}
        if any(x in title_lower for x in ['marketing', 'growth', 'acquisition', 'ad', 'brand']):
            strategy = self.playbook.get('personas', {}).get('marketing', {})
        elif any(x in title_lower for x in ['e-commerce', 'cro', 'conversion', 'shop', 'director', 'manager']):
            strategy = self.playbook.get('personas', {}).get('ecommerce', {})
        else:
            strategy = self.playbook.get('personas', {}).get('founder', {})

        reviews_tech = domain_score.details.get('shopscope_reviews', 'None')
        competitor_tech = domain_score.details.get('shopscope_competitor', 'None')
        cro_tech = domain_score.details.get('shopscope_cro', 'None')
        email_tech = domain_score.details.get('shopscope_email', 'None')
        pixels_tech = domain_score.details.get('shopscope_pixels', 'None')
        pagespeed_info = domain_score.details.get('pagespeed_details', '')

        if "Staffing" in business_type or "Services" in business_type:
            headline = f"Increasing Client & Candidate Conversion for {clean_domain}"
            pain_point = (
                "static web pages fail to engage high-intent corporate clients and top talent candidates. "
                "Zeacon's interactive video players turn existing social and client video testimonials into engaging website feeds, "
                "driving an 8% to 12% increase in conversion."
            )
        elif "Automotive" in business_type:
            headline = f"Converting High-Intent Vehicle Shoppers for {clean_domain}"
            pain_point = "prospective buyers want interactive video walkthroughs before booking a showroom visit or test drive."
        elif "Hospitality" in business_type:
            headline = f"Driving Reservation Checkouts for {clean_domain}"
            pain_point = "text menus fail to convey the dining experience compared to interactive video reels."
        elif competitor_tech != 'None':
            headline = f"Maximize {clean_domain} Video Conversion ROI"
            pain_point = f"currently using {competitor_tech} static widgets which don't dynamically adapt to visitor intent."
        else:
            headline = f"Conversion Uplift Opportunity for {clean_domain}"
            pain_point = "landing pages currently lack interactive video widgets, causing high-intent visitors to bounce."

        focus = case_study.get('focus', 'video engagement')
        metric = case_study.get('metric', '8% to 12% increase in conversion')
        title = case_study.get('title')
        desc = case_study.get('description', '')

        historical_feedback = self._compile_historical_feedback()

        tweak_instruction = ""
        if user_tweak:
            tweak_instruction = f"CRITICAL USER TWEAK INSTRUCTION: The user wants to adjust the message with these thoughts: '{user_tweak}'. Rewrite and modify the email body incorporating these ideas.\n"

        framework_instructions = (
          "SALES METHODOLOGY GUIDELINES:\n"
          f"- Business Model & Social Context: Prospect is a '{business_type}' operating on '{conversion_model}'. Active Social Channels: {social_platforms}. Insight: {social_correlation}.\n"
          "- Emulate Kris's Proven Sales Style: Highlight how Zeacon personalizes website content in real time using video assets already in their Instagram, Facebook, and YouTube libraries.\n"
          "- Empirical Split-Test Proof: Cite controlled 30-day split-testing showing Zeacon video viewers convert at +66% higher rates (10.43% vs 4.42% control) and generate +56% more inquiries.\n"
          "- Conversion Science: Reference that 82% of buyers are convinced after watching video, and extending time-on-site (TOS) logarithmically elevates conversion probability while lowering CAC.\n"
          "- SPIN Selling Framework: 1) State an observed Situation, 2) Identify the Problem/gap, 3) Highlight Implication, 4) Present Zeacon as Need-Payoff.\n"
        )

        system_prompt = (
            "You are a Senior Enterprise Sales Executive at Zeacon (zeacon.com).\n"
            "Write a short, professional, consultative cold sales email to the prospect provided.\n"
            "Write ONLY the email body. Do NOT write subject lines or header text.\n"
            "Adhere strictly to these principles:\n"
            "- Word limit: 120 words maximum.\n"
            "- Tone: Consultative, direct, warm, and outcome-oriented.\n"
            "- Sign off exactly as '[Your Name]\nSales Team | Zeacon'.\n\n"
            f"{framework_instructions}\n"
            f"{historical_feedback}"
            f"{tweak_instruction}"
        )

        user_prompt = (
            f"Prospect Name: {contact.name}\n"
            f"Prospect Title: {contact.title}\n"
            f"Prospect Company: {clean_domain} ({domain_score.domain})\n"
            f"Business Category: {business_type} (Primary Goal: {conversion_model})\n"
            f"Active Social Video Platforms: {social_platforms}\n"
            f"Company News Context: {brand_news[:250]}\n"
            f"Tech Stack Detected: Reviews: {reviews_tech}, Video Widget: {competitor_tech}, CRO: {cro_tech}, Email/SMS: {email_tech}, Pixels: {pixels_tech}\n"
            f"Site Performance Audit: {pagespeed_info}\n"
            f"Role Focus & Pain Points: {strategy.get('focus', '')} - Tactic: {strategy.get('tactic', '')}\n"
            f"Tailored Gap & Hook Tactic: {pain_point}\n"
            f"Zeacon Case Study to reference: '{title}' (Focus: {focus}, Result: {metric}, Details: {desc})\n"
            f"Write the email body now:"
        )

        llm_body = ""

        if self.provider == "claude" or (self.provider == "auto" and self.anthropic_key):
            llm_body = self._query_claude(system_prompt, user_prompt)

        if not llm_body and (self.provider == "gemini" or (self.provider == "auto" and self.gemini_key)):
            llm_body = self._query_gemini(system_prompt, user_prompt)

        if not llm_body:
            full_llama_prompt = f"<|system|>\n{system_prompt}\n<|user|>\n{user_prompt}\n<|assistant|>\n"
            llm_body = self._query_local_llm(full_llama_prompt)

        if not llm_body:
            llm_body = (
                f"Hi {contact.name},\n\n"
                f"Zeacon's been helping brands increase sales and client conversion by personalizing video content for every visitor that enters their site, repurposing video assets already in your Instagram, Facebook, and YouTube libraries.\n\n"
                f"Our customers see an 8% to 12% increase in online conversion. "
                f"It's extremely cost-effective and helps engage prospective clients and talent to make decisions faster while lowering customer acquisition costs (CAC).\n\n"
                f"Would you be open to a quick 10-minute audit next Tuesday to explore how Zeacon can enhance {clean_domain}'s digital experience?\n\n"
                f"[Your Name]\n"
                f"Sales Team | Zeacon"
            )

        # Generate personalized <300 character LinkedIn Connection Note for Kris Naidu
        first_name = contact.name.split()[0] if contact.name else "there"
        biz_short = "e-commerce" if "D2C" in business_type or "Cart" in conversion_model else "digital growth"
        
        linkedin_text = (
            f"Hi {first_name}, I'm Kris Naidu, CEO of Zeacon. Noticed {clean_domain}'s work in {biz_short} - we help brands turn social video into on-site revenue (avg +25% lift) with zero site speed impact. Would love to connect and share a quick video ROI audit for {clean_domain}!"
        )
        if len(linkedin_text) > 298:
            linkedin_text = (
                f"Hi {first_name}, I'm Kris Naidu, CEO of Zeacon. We help brands like {clean_domain} convert website visitors using interactive video (avg +25% lift). Would love to connect!"
            )

        return OutreachDraft(
            persona=contact.title,
            subject=headline,
            body=llm_body,
            linkedin_note=linkedin_text
        )

    def generate_executive_brief(self, domain_score: DomainScore, contact: Contact) -> str:
        """
        B2B Chief Revenue Officer & Marketing Strategist Persona.
        Analyzes domain telemetry (tech stack, traffic, video presence, social channels)
        and outputs a 3-bullet executive sales strategy brief for the rep.
        """
        clean_domain = domain_score.domain.split('.')[0].capitalize()
        if clean_domain.lower() == 'roberthalf':
            clean_domain = "Robert Half"

        biz_type = domain_score.details.get('business_type', 'Commercial Business')
        conv_model = domain_score.details.get('conversion_model', 'Digital Storefront')
        traffic_raw = domain_score.details.get('traffic_tech', 'Standard Traffic')
        socials = domain_score.details.get('social_active_platforms', 'Social Video Platforms')
        reviews = domain_score.details.get('shopscope_reviews', 'None')
        cro = domain_score.details.get('shopscope_cro', 'None')
        email = domain_score.details.get('shopscope_email', 'None')
        pixels = domain_score.details.get('shopscope_pixels', 'None')

        system_prompt = (
            "You are a Chief Revenue Officer and Senior B2B Marketing Strategist.\n"
            "Review the raw technical audit data of a prospect domain and provide 3 sharp, executive-level strategic takeaways for a B2B sales representative pitching Zeacon's interactive video platform.\n"
            "Format your response as exactly 3 concise, bulleted insights:\n"
            "1. 💡 **Strategic Opportunity & CAC Risk**: Where is the prospect leaking conversion or ROAS?\n"
            "2. 🛠️ **Tech Stack Ecosystem**: How does Zeacon integrate with their detected tech stack?\n"
            "3. 🎯 **Consultative Pitch Angle**: What exact value proposition should the sales rep lead with?\n"
            "Keep each point under 35 words. Be direct, authoritative, and strategic."
        )

        user_prompt = (
            f"Company: {clean_domain} ({domain_score.domain})\n"
            f"Business Category: {biz_type} (Goal: {conv_model})\n"
            f"Audience Traffic Tier: {traffic_raw}\n"
            f"Active Social Video Platforms: {socials}\n"
            f"Detected Tech Stack: Reviews={reviews}, CRO={cro}, Email={email}, Pixels={pixels}\n"
            f"Target Executive: {contact.name} ({contact.title})"
        )

        if self.provider == "claude" or (self.provider == "auto" and HAS_ANTHROPIC and self.anthropic_key):
            result = self._query_claude(system_prompt, user_prompt)
            if result:
                return result

        if self.provider in ["gemini", "auto"] and HAS_GEMINI and self.gemini_key:
            result = self._query_gemini(system_prompt, user_prompt)
            if result:
                return result

        # Heuristic fallback if offline or local Llama
        return (
            f"1. 💡 **Strategic Opportunity**: {clean_domain} is active on {socials} — repurpose existing social video assets into on-site interactive feeds to capture 8-12% higher conversion.\n"
            f"2. 🛠️ **Tech Stack Ecosystem**: Integrates natively alongside {reviews if reviews != 'None' else 'detected'} review engines & {email if email != 'None' else 'marketing'} tools with zero script bloat.\n"
            f"3. 🎯 **Consultative Pitch Angle**: Lead with Zeacon's ability to lower CAC and turn static storefront visitors into engaged video buyers."
        )

    def generate_followup_draft(self, sequence: Dict[str, Any], domain_score: Optional[DomainScore] = None, step: int = 2) -> Dict[str, str]:
        """
        Generates contextual follow-up messages for Touch 2 (Social proof bump),
        Touch 3 (Technical ease/speed handle), and Touch 4 (Executive breakup/audit).
        """
        contact_name = sequence.get('contact_name', 'there')
        first_name = contact_name.split()[0] if contact_name else "there"
        domain = sequence.get('domain', '')
        clean_domain = domain.split('.')[0].capitalize()
        
        # Touch 2: Social Proof & Split Test Metrics (+3 days)
        if step == 2:
            email_subj = f"Re: Conversion uplift opportunity for {clean_domain}"
            email_body = (
                f"Hi {first_name},\n\n"
                f"Following up on my previous note. Wanted to quickly share some recent data that might be relevant for {clean_domain}:\n\n"
                f"In our latest 30-day controlled split test (13,847 visitor sessions), adding interactive video feeds generated a +66% lift in online purchase rates and 2x higher visitor dwell time compared to static pages.\n\n"
                f"Because Zeacon automatically connects to your existing social video library (Instagram, TikTok, YouTube), there's zero content production required on your end.\n\n"
                f"Would you be open to a 5-minute preview this week?\n\n"
                f"Best,\nKris Naidu\nCEO | Zeacon\n+1 206 487 1742 · Bellevue, WA"
            )
            linkedin_msg = (
                f"Hi {first_name}, following up on my note! We recently ran a 30-day split test showing +66% order lift when adding interactive social video to storefronts. Would love to show you how {clean_domain} can do this with zero new video production."
            )
            
        # Touch 3: Speed & Technical Ease (<50ms async player, $49/mo) (+4 days)
        elif step == 3:
            email_subj = f"Zero-code video commerce for {clean_domain}"
            email_body = (
                f"Hi {first_name},\n\n"
                f"Most marketing leaders we speak with love video but worry about site speed and developer resources.\n\n"
                f"Zeacon was built specifically to solve this: our lightweight asynchronous player loads in under 50ms (zero impact on Core Web Vitals) and installs in under 5 minutes on Shopify, Webflow, WordPress, or custom platforms with a single line of code.\n\n"
                f"Plans start at just $49/mo (5,000 sessions, unlimited players), making it a zero-risk way to test interactive video on {clean_domain}.\n\n"
                f"Do you have 10 minutes next Tuesday for a quick look?\n\n"
                f"Best,\nKris Naidu\nCEO | Zeacon\nCalendly: https://calendly.com/krisnaidu/zeacon"
            )
            linkedin_msg = (
                f"Hi {first_name}, quick technical note: Zeacon loads asynchronously in <50ms with zero impact on site speed, and integrates in 5 mins. Happy to send over a 1-minute live demo on {clean_domain} if interested!"
            )
            
        # Touch 4: Executive Breakup / Free Personalized Audit (+7 days)
        else:
            email_subj = f"Closing the loop on {clean_domain} video audit"
            email_body = (
                f"Hi {first_name},\n\n"
                f"I realize you're likely focused on other priorities right now, so I'll close the loop here.\n\n"
                f"If you'd ever like to see where {clean_domain} might be losing conversions on static landing pages, I'd be happy to prepare a complimentary Video ROI Audit for your team down the road.\n\n"
                f"Wishing you and the {clean_domain} team continued growth!\n\n"
                f"Best regards,\nKris Naidu\nCEO | Zeacon\nhttps://www.zeacon.com"
            )
            linkedin_msg = (
                f"Hi {first_name}, closing the loop here! If optimizing visitor conversion with interactive video ever becomes a priority for {clean_domain}, feel free to reach out anytime. Wishing you great success!"
            )
            
        return {
            "step": step,
            "email_subject": email_subj,
            "email_body": email_body,
            "linkedin_message": linkedin_msg
        }
