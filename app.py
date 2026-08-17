import streamlit as st
import database as db
from scoring import DomainScorer
from enrichment import ContactEnricher
from ammo_vault import AmmoVault
from generator import OutreachGenerator
from models import DomainScore, Contact
import urllib.parse
import pandas as pd
import json
import os

# Setup page config
st.set_page_config(
    page_title="Zeacon Prospector",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database
import importlib
importlib.reload(db)
db.init_db()

# Password Protection Gate for Client Access
def check_password():
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False

    if not st.session_state["password_correct"]:
        st.markdown("""
        <div style='text-align:center; padding:2.5rem 1rem 1rem 1rem;'>
            <h1 style='color:#e11d48; font-size:2.2rem; font-weight:800; margin-bottom:0.2rem;'>🔒 Zeacon Prospector</h1>
            <p style='color:#475569; font-size:1rem; font-weight:500;'>Executive B2B Sales Intelligence Portal</p>
        </div>
        """, unsafe_allow_html=True)
        
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            st.markdown("""
            <div style='background:#ffffff; border:1px solid #cbd5e1; border-radius:12px; padding:1.75rem; box-shadow:0 4px 6px -1px rgba(0, 0, 0, 0.1);'>
                <div style='font-size:0.9rem; font-weight:700; color:#0f172a; margin-bottom:0.75rem;'>🔑 Client Access Authentication</div>
            """, unsafe_allow_html=True)
            
            pwd = st.text_input("Enter Password", type="password", key="pwd_gate")
            if st.button("Unlock Portal", type="primary", use_container_width=True):
                valid_pwd = os.getenv("DEMO_PASSWORD", "Zeacon2026!")
                if pwd == valid_pwd:
                    st.session_state["password_correct"] = True
                    st.rerun()
                else:
                    st.error("❌ Incorrect password. Please try again.")
            st.markdown("</div>", unsafe_allow_html=True)
        return False
    return True

if not check_password():
    st.stop()

# Main Styling Customizations mimicking Zeacon's website
st.markdown("""
<style>
    /* Main Background & Fonts */
    .stApp {
        background-color: #fcfdfd;
        color: #111111;
    }
    
    /* Header branding */
    .zeacon-header {
        font-family: 'Outfit', 'Inter', sans-serif;
        font-weight: 800;
        font-size: 2.8rem;
        color: #000000;
        margin-bottom: 0.1rem;
    }
    .zeacon-red-dot {
        color: #e11d48;
    }
    
    /* See results tag */
    .results-badge {
        background: linear-gradient(90deg, #dbeafe 0%, #ffe4e6 100%);
        color: #1e3a8a;
        padding: 0.4rem 1rem;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        display: inline-block;
        margin-bottom: 1rem;
    }

    /* Business category badge */
    .category-badge {
        background-color: #0f172a;
        color: #ffffff;
        padding: 0.35rem 0.85rem;
        border-radius: 6px;
        font-size: 0.8rem;
        font-weight: 700;
        display: inline-block;
        margin-top: 0.25rem;
    }

    /* Subheaders */
    h1, h2, h3, h4 {
        font-family: 'Outfit', 'Inter', sans-serif;
        font-weight: 700;
        color: #0f172a;
    }

    /* Cards */
    .metric-card {
        background-color: #ffffff;
        border-radius: 12px;
        padding: 1.5rem;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
        text-align: center;
        margin-bottom: 1rem;
    }
    .metric-title {
        font-size: 0.825rem;
        color: #475569;
        font-weight: 600;
        text-transform: uppercase;
        margin-bottom: 0.5rem;
    }
    .metric-value {
        font-size: 2.5rem;
        font-weight: 800;
        color: #0f172a;
    }

    /* Consultative Insight Cards */
    .insight-box {
        background-color: #f8fafc;
        border-left: 4px solid #e11d48;
        padding: 1.25rem;
        margin-bottom: 1rem;
        border-radius: 0 10px 10px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }
    .secondary-insight-box {
        background-color: #ffffff;
        border: 1px solid #cbd5e1;
        border-left: 4px solid #64748b;
        padding: 0.9rem 1.1rem;
        margin-bottom: 0.75rem;
        border-radius: 0 8px 8px 0;
    }
    
    /* Audit Finding Cards */
    .finding-card {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 0.85rem 1.1rem;
        margin-bottom: 0.75rem;
    }
    .finding-title {
        font-size: 0.85rem;
        font-weight: 700;
        color: #1e293b;
        text-transform: uppercase;
        letter-spacing: 0.03em;
    }
    .finding-desc {
        font-size: 0.925rem;
        color: #334155;
        margin-top: 0.25rem;
    }
    .finding-takeaway {
        font-size: 0.825rem;
        color: #64748b;
        font-style: italic;
        margin-top: 0.35rem;
        background-color: #f8fafc;
        padding: 0.35rem 0.65rem;
        border-radius: 4px;
    }

    /* Living Tutorial Tooltips (Hover Popovers) */
    [data-tooltip] {
        position: relative;
        cursor: help;
    }

    [data-tooltip]::after {
        content: attr(data-tooltip);
        position: absolute;
        bottom: 110%;
        left: 50%;
        transform: translateX(-50%) translateY(4px);
        background-color: #0f172a;
        color: #ffffff;
        padding: 0.7rem 0.9rem;
        border-radius: 8px;
        font-size: 0.78rem;
        font-weight: 500;
        line-height: 1.45;
        white-space: normal;
        width: 250px;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3), 0 8px 10px -6px rgba(0, 0, 0, 0.2);
        z-index: 99999;
        pointer-events: none;
        opacity: 0;
        visibility: hidden;
        transition: opacity 0.25s ease, transform 0.25s ease, visibility 0.25s ease;
        text-align: left;
    }

    [data-tooltip]:hover::after {
        opacity: 1;
        visibility: visible;
        transform: translateX(-50%) translateY(0);
    }

    /* Primary actions */
    div.stButton > button:first-child {
        background-color: #000000;
        color: #ffffff;
        border-radius: 8px;
        font-weight: 600;
        border: none;
        padding: 0.5rem 1.5rem;
    }
    div.stButton > button:first-child:hover {
        background-color: #222222;
        color: #ffffff;
    }
    
    /* LinkedIn Pop Link Styles */
    .linkedin-link-btn {
        display: inline-block;
        background-color: #0077b5;
        color: white !important;
        font-weight: 600;
        padding: 0.55rem 1.1rem;
        border-radius: 8px;
        text-decoration: none;
        font-size: 0.9rem;
        margin-top: 0.75rem;
        text-align: center;
    }
    .linkedin-link-btn:hover {
        background-color: #005a87;
    }
    
    /* Meta ad link styles */
    .meta-ad-link-btn {
        display: inline-block;
        background-color: #3b5998;
        color: white !important;
        font-weight: 600;
        padding: 0.4rem 0.8rem;
        border-radius: 6px;
        text-decoration: none;
        font-size: 0.8rem;
        margin-top: 0.5rem;
    }
    .meta-ad-link-btn:hover {
        background-color: #2d4373;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar Configuration for Cloud & Model API Selection
st.sidebar.markdown("<h2>zeac<span style='color:#e11d48;'>o</span>n</h2>", unsafe_allow_html=True)

model_provider = st.sidebar.selectbox(
    "🤖 Copywriting AI Model",
    options=["auto", "claude", "gemini", "llama"],
    format_func=lambda x: {
        "auto": "⚡ Auto-Detect (Claude -> Gemini -> Llama)",
        "claude": "🧠 Claude 3.5 Sonnet (Recommended)",
        "gemini": "🚀 Google Gemini 2.5 Flash",
        "llama": "💻 Local Llama 3.2 (Offline Dev)"
    }[x],
    index=0
)

def safe_get_secret(key_name: str) -> str:
    try:
        if hasattr(st, "secrets") and key_name in st.secrets:
            return st.secrets[key_name]
    except Exception:
        pass
    return os.getenv(key_name, "")

anthropic_key = safe_get_secret("ANTHROPIC_API_KEY")
gemini_key = safe_get_secret("GEMINI_API_KEY")
apollo_key = safe_get_secret("APOLLO_API_KEY")
hunter_key = safe_get_secret("HUNTER_API_KEY") or "337e848af7d3c8af38e1c8234255b30f1631ab34"

with st.sidebar.expander("🔑 API Key Settings"):
    user_anthropic = st.text_input("Anthropic API Key", value=anthropic_key, type="password")
    user_gemini = st.text_input("Google Gemini API Key", value=gemini_key, type="password")
    user_apollo = st.text_input("Apollo.io API Key", value=apollo_key, type="password", help="Paid Apollo plan required for database prospecting")
    user_hunter = st.text_input("Hunter.io API Key", value=hunter_key, type="password", help="Free/Paid Hunter key for verified email patterns")
    if user_anthropic:
        anthropic_key = user_anthropic
    if user_gemini:
        gemini_key = user_gemini
    if user_apollo:
        apollo_key = user_apollo
    if user_hunter:
        hunter_key = user_hunter

    # Live Credit Meter inside expander (Cached 5 mins)
    @st.cache_data(ttl=300)
    def fetch_cached_hunter_stats(key: str):
        try:
            import requests
            h_resp = requests.get(f"https://api.hunter.io/v2/usage?api_key={key}", timeout=4)
            if h_resp.status_code == 200:
                return h_resp.json().get("data", {})
        except Exception:
            pass
        return {}

    if hunter_key:
        try:
            h_data = fetch_cached_hunter_stats(hunter_key)
            if h_data:
                h_credits = h_data.get("credits", {})
                h_reqs = h_data.get("requests", {})
                used = h_credits.get("used", h_reqs.get("used", 0))
                total = h_credits.get("available", h_reqs.get("available", 50))
                remaining = h_credits.get("remaining", max(0, total - used))
                reset_date = h_data.get("reset_date", "End of month")
                pct = min(100, int((used / total) * 100)) if total else 0

                bar_color = "#dc2626" if remaining == 0 else ("#d97706" if remaining <= 5 else "#0d9488")
                
                st.markdown(f"""
                <div style='background:#f8fafc; border:1px solid #cbd5e1; border-radius:8px; padding:0.75rem; margin-top:0.75rem;'>
                    <div style='font-size:0.8rem; font-weight:700; color:#0f172a; margin-bottom:0.25rem;'>📊 Hunter.io Credit Usage</div>
                    <div style='font-size:0.75rem; color:#475569;'><strong>{used}</strong> / {total} credits used ({remaining} remaining)</div>
                    <div style='background:#e2e8f0; border-radius:4px; height:8px; margin:0.4rem 0; overflow:hidden;'>
                        <div style='background:{bar_color}; width:{pct}%; height:100%;'></div>
                    </div>
                    <div style='font-size:0.7rem; color:#64748b;'>Resets: {reset_date}</div>
                </div>
                """, unsafe_allow_html=True)
                
                if remaining == 0:
                    st.warning("⚠️ Hunter.io free credits depleted! Upgrade key or wait for reset date.")
        except Exception:
            pass

use_live_apis = st.sidebar.toggle("Use Live APIs", value=True)

# In-The-Moment Client Feedback & Wishlist Submission
with st.sidebar.expander("💬 Submit App Feedback (Kris / Client)", expanded=False):
    st.markdown("<div style='font-size:0.8rem; font-weight:700; color:#0f172a; margin-bottom:0.4rem;'>Record In-The-Moment Feedback</div>", unsafe_allow_html=True)
    fb_domain = st.session_state.get('current_domain', 'General Platform')
    fb_category = st.selectbox("Feedback Area", ["🎯 Scoring & Telemetry", "👤 Contact Enrichment", "✉️ Outreach Copy & Briefing", "🎨 UI & Design", "🐛 Bug / Feature Request"], key="fb_cat")
    fb_rating = st.selectbox("Rating", ["⭐⭐⭐⭐⭐ Excellent", "👍 Good / Minor Change", "💡 Suggestion / Idea", "⚠️ Needs Revision"], key="fb_rate")
    fb_text = st.text_area("Your Notes / Desired Updates", placeholder="What is working well? What needs to be adjusted?", key="fb_notes", height=100)
    
    if st.button("Submit Feedback Entry", type="primary", use_container_width=True, key="btn_submit_client_fb"):
        if fb_text.strip():
            if hasattr(db, 'log_client_feedback'):
                db.log_client_feedback(fb_domain, fb_category, fb_rating, fb_text)
            st.toast("✅ Feedback logged successfully! Database updated.")
            st.success("Feedback recorded! Thank you, Kris.")
        else:
            st.warning("Please enter your notes before submitting.")

# Admin View Submitted Feedback Logs
with st.sidebar.expander("📋 View Submitted Feedback Log", expanded=False):
    feedback_entries = db.get_client_feedback() if hasattr(db, 'get_client_feedback') else []
    if feedback_entries:
        st.markdown(f"**Total Feedback Entries:** `{len(feedback_entries)}`")
        fb_df = pd.DataFrame(feedback_entries)
        st.dataframe(fb_df[['timestamp', 'category', 'rating', 'feedback', 'domain']], use_container_width=True)
        csv_fb = fb_df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Export Feedback to CSV", csv_fb, "client_feedback_log.csv", "text/csv", key="dl_fb_csv")
    else:
        st.info("No feedback submissions logged yet.")

st.sidebar.info("Turn your storefront videos into revenue with consultative outreach.")

st.markdown("<div class='results-badge'>See Results Immediately</div>", unsafe_allow_html=True)

st.markdown("<h1 class='zeacon-header'>zeac<span class='zeacon-red-dot'>o</span>n prospector</h1>", unsafe_allow_html=True)
st.markdown("<p style='color:#475569; font-size:1.1rem; margin-bottom: 2rem;'>Turn your videos into revenue. Qualify e-commerce stores and draft custom campaigns.</p>", unsafe_allow_html=True)

tab_prospect, tab_sequences, tab_analytics, tab_ammo = st.tabs(["🔍 Prospect Analyzer", "📅 Sequences & Follow-Ups", "📊 Historical Database", "⚡ Proof Points & Winning Vault"])

with tab_prospect:
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Analyze E-Commerce Brand")
        url_input = st.text_input("Enter Brand Domain (e.g. gymshark.com, eastsidegolf.com, roberthalf.com, arniesrestaurant.com)", placeholder="branddomain.com")
        analyze_btn = st.button("Run Pipeline & Score Match", type="primary")

    if analyze_btn and url_input:
        domain = url_input.strip().lower()
        if "://" in domain:
            domain = domain.split("://")[-1]
        domain = domain.split('/')[0].split('?')[0].strip()
        if domain.startswith("www."):
            domain = domain[4:]

        with st.spinner(f"Analyzing {domain} & fetching leads..."):
            st.session_state['active_contact_idx'] = 0
            st.session_state['custom_tweak_input'] = ""
            st.session_state['selected_strategy_angle'] = None
            st.session_state['show_critique_box'] = False
            st.session_state['show_strat_critique_box'] = False
            
            # Clear cached executive briefs & drafts from previous runs
            keys_to_clear = [k for k in st.session_state.keys() if k.startswith('exec_brief_') or k in ['current_draft', 'last_log_id', 'current_score']]
            for k in keys_to_clear:
                del st.session_state[k]
                
            import importlib
            import scoring
            import enrichment
            import generator
            importlib.reload(scoring)
            importlib.reload(enrichment)
            importlib.reload(generator)

            scorer = scoring.DomainScorer(use_live_apis=use_live_apis)
            score_res = scorer.score_domain(domain)
            db.log_prospect(score_res)

            enricher = enrichment.ContactEnricher(use_live_apis=use_live_apis, apollo_key=apollo_key, hunter_key=hunter_key)
            contacts = enricher.fetch_contacts(domain)
            db.log_contacts(domain, contacts)

            st.success("Pipeline executed successfully! Data logged to local SQLite Database.")
            
            st.session_state['current_domain'] = domain
            st.session_state['current_score'] = score_res
            st.session_state['current_contacts'] = contacts

    if 'current_score' in st.session_state and 'current_contacts' in st.session_state:
        score_res = st.session_state['current_score']
        contacts = st.session_state['current_contacts']
        domain = st.session_state['current_domain']

        verified_profiles_list = [
            "m-keith-waddell", "megan-slabinski-7140884", "brettgood",
            "olajuwon-ajanaku-b747045b", "earl-cooper-pga-15a0a34b", "kendragarnett",
            "ben-francis-023a1052", "nollaigfahy", "sian-keane-44163914"
        ]

        st.markdown("---")
        
        biz_type = score_res.details.get('business_type', 'Commercial Enterprise')
        conv_model = score_res.details.get('conversion_model', 'Digital Conversion Engine')

        clean_d = domain.split('/')[0].lower().replace('www.', '')
        logo_url = f"https://www.google.com/s2/favicons?domain={clean_d}&sz=128"
        
        header_col1, header_col2 = st.columns([1, 8])
        with header_col1:
            st.markdown(
                f'<div style="background:#ffffff; border:1px solid #e2e8f0; border-radius:12px; width:64px; height:64px; display:flex; align-items:center; justify-content:center; box-shadow:0 2px 4px rgba(0,0,0,0.04);">'
                f'<img src="{logo_url}" style="max-width:44px; max-height:44px; border-radius:6px;" onerror="this.onerror=null; this.src=\'https://logo.clearbit.com/{clean_d}\';">'
                f'</div>',
                unsafe_allow_html=True
            )
        with header_col2:
            st.markdown(f"### Score Card for **{domain}**")
            st.markdown(f"<div class='category-badge'>🏢 Business Category: {biz_type} | Goal: {conv_model}</div>", unsafe_allow_html=True)

        m_col1, m_col2, m_col3, m_col4, m_col5 = st.columns(5)
        with m_col1:
            st.markdown(f"<div class='metric-card' data-tooltip='🎯 Composite ICP Score (0-100): Calculated from Video Ads (30pt), Audience Traffic Scale (25pt), On-Site Video (25pt), and Conversion Engine (20pt).'><div class='metric-title'>Match Score ℹ️</div><div class='metric-value' style='color:#e11d48;'>{score_res.total_score}</div><div style='color:#64748b; font-size:0.8rem;'>Max 100</div></div>", unsafe_allow_html=True)
        with m_col2:
            st.markdown(f"<div class='metric-card' data-tooltip='📢 Paid Video Advertising (30pt): Scans DOM for active Meta/TikTok ad pixels and checks for active video campaigns in Meta Ad Library.'><div class='metric-title'>Video Ads ℹ️</div><div class='metric-value'>{score_res.video_ads_score}</div><div style='color:#64748b; font-size:0.8rem;'>Max 30</div></div>", unsafe_allow_html=True)
        with m_col3:
            st.markdown(f"<div class='metric-card' data-tooltip='📈 Audience Scale (25pt): Evaluates global monthly visitor scale via OpenPageRank API and AI Brand Intelligence.'><div class='metric-title'>Web Traffic ℹ️</div><div class='metric-value'>{score_res.traffic_score}</div><div style='color:#64748b; font-size:0.8rem;'>Max 25</div></div>", unsafe_allow_html=True)
        with m_col4:
            st.markdown(f"<div class='metric-card' data-tooltip='🎬 On-Site Video (25pt): Scans DOM for video tags, YouTube, Vimeo, Bambuser, Tolstoy, and Bazaarvoice UGC Video Reels.'><div class='metric-title'>On-Site Video ℹ️</div><div class='metric-value'>{score_res.onsite_video_score}</div><div style='color:#64748b; font-size:0.8rem;'>Max 25</div></div>", unsafe_allow_html=True)
        with m_col5:
            card_title = "Conversion Engine" if "Staffing" in biz_type or "SaaS" in biz_type or "Hospitality" in biz_type else "E-comm Cart"
            st.markdown(f"<div class='metric-card' data-tooltip='🛒 Conversion Engine (20pt): Identifies primary checkout or lead capture setup (Shopify, Custom Cart, Booking Engine, Staffing Portal).'><div class='metric-title'>{card_title} ℹ️</div><div class='metric-value'>{score_res.cart_score}</div><div style='color:#64748b; font-size:0.8rem;'>Max 20</div></div>", unsafe_allow_html=True)

        st.markdown("### 📋 Executive Sales Intelligence")
        
        in_col1, in_col2 = st.columns(2)
        with in_col1:
            st.markdown("#### 🔍 Plain-English Storefront Audit")
            
            cart_raw = score_res.details.get('cart_tech', 'Unknown')
            st.markdown(f"""
            <div class='finding-card' data-tooltip='⚙️ Conversion Engine Audit: Evaluates whether the prospect uses Shopify Plus, WooCommerce, Custom E-Comm, Staffing Portals, or Booking Systems.'>
                <div class='finding-title'>⚙️ Primary Conversion Model & Platform ℹ️</div>
                <div class='finding-desc'><strong>Detected Setup:</strong> {cart_raw}</div>
                <div class='finding-takeaway'>💡 <em>What this means:</em> Evaluated for {conv_model} capabilities.</div>
            </div>
            """, unsafe_allow_html=True)

            social_platforms = score_res.details.get('social_active_platforms', 'None')
            social_corr = score_res.details.get('social_correlation', '')
            st.markdown(f"""
            <div class='finding-card' data-tooltip='📱 Social Asset Library: Scans for active Instagram, TikTok, Facebook, and YouTube channels. Zeacon automatically imports these existing video assets to populate website widgets.'>
                <div class='finding-title'>📱 Social Media Video Asset Library ℹ️</div>
                <div class='finding-desc'><strong>Active Platforms:</strong> {social_platforms}</div>
                <div class='finding-takeaway'>💡 <em>Zeacon Opportunity Correlation:</em> {social_corr}</div>
            </div>
            """, unsafe_allow_html=True)

            video_raw = score_res.details.get('video_onsite_tech', 'No video tracked')
            video_takeaway = "Great candidate for Zeacon! Floating video widgets will convert static site visitors." if score_res.onsite_video_score < 15 else "High video usage detected — prime candidate for Zeacon's ROI attribution analytics."
            st.markdown(f"""
            <div class='finding-card' data-tooltip='🎬 On-Site Video Audit: Detects if the website already has embedded video players, YouTube/Vimeo embeds, or competitor widgets like Tolstoy/Bambuser/Bazaarvoice.'>
                <div class='finding-title'>🎬 Website Video Presence ℹ️</div>
                <div class='finding-desc'><strong>Current Setup:</strong> {video_raw}</div>
                <div class='finding-takeaway'>💡 <em>What this means:</em> {video_takeaway}</div>
            </div>
            """, unsafe_allow_html=True)

            speed_raw = score_res.details.get('pagespeed_details', 'Optimized')
            st.markdown(f"""
            <div class='finding-card' data-tooltip='⚡ Site Speed & Load Health: Evaluates total script count to ensure Zeacon lightweight asynchronous player (<50ms) will load smoothly.'>
                <div class='finding-title'>⚡ Site Speed & Load Health ℹ️</div>
                <div class='finding-desc'><strong>Status:</strong> {speed_raw}</div>
                <div class='finding-takeaway'>💡 <em>What this means:</em> Pitch Zeacon's lightweight player that loads asynchronously under 50ms without slowing down their portal.</div>
            </div>
            """, unsafe_allow_html=True)

            ad_raw = score_res.details.get('video_ads_tech', 'Limited ads detected')
            pixels_str = score_res.details.get('shopscope_pixels', '')
            has_meta_pixel = 'Meta Pixel' in pixels_str or 'Verified Meta Video Ads' in ad_raw or 'Verified Ad Campaign Signals' in ad_raw

            ad_badge = "<span style='background:#059669; color:white; font-size:0.7rem; font-weight:700; padding:2px 8px; border-radius:4px;'>✓ VERIFIED ACTIVE ADVERTISER</span>" if has_meta_pixel else "<span style='background:#d97706; color:white; font-size:0.7rem; font-weight:700; padding:2px 8px; border-radius:4px;'>⚠️ UNVERIFIED SIGNAL</span>"
            
            ad_takeaway = "Active Meta/TikTok advertising pixel detected on site — high ad spend driving video traffic." if has_meta_pixel else "No Meta Pixel script detected in DOM. Verify active video campaigns manually in Meta Ad Library."

            st.markdown(f"""
            <div class='finding-card' data-tooltip='📢 Paid Video Advertising: Scans DOM for Meta/TikTok advertising pixels. Active pixels confirm the brand is spending ad dollars driving paid video traffic.'>
                <div class='finding-title'>📢 Paid Video Advertising Check {ad_badge} ℹ️</div>
                <div class='finding-desc'><strong>Status:</strong> {ad_raw}</div>
                <div class='finding-takeaway'>💡 <em>What this means:</em> {ad_takeaway}</div>
            </div>
            """, unsafe_allow_html=True)

            clean_brand = domain.split('.')[0].capitalize()
            manual_fb_query = urllib.parse.quote_plus(clean_brand)
            ad_url = f"https://www.facebook.com/ads/library/?active_status=active&ad_type=all&q={manual_fb_query}&search_type=keyword_unordered&media_type=video"
            st.markdown(
                f'<a href="{ad_url}" target="_blank" class="meta-ad-link-btn">🔗 Open Live Video Ads for {clean_brand} in Meta Ad Library ↗</a>',
                unsafe_allow_html=True
            )

            traffic_raw = score_res.details.get('traffic_tech', 'Standard')
            st.markdown(f"""
            <div class='finding-card' style='margin-top:0.75rem;'>
                <div class='finding-title'>📈 Estimated Monthly Visitors</div>
                <div class='finding-desc'><strong>Audience Rank:</strong> {traffic_raw}</div>
                <div class='finding-takeaway'>💡 <em>What this means:</em> Helps gauge business scale to tailor our pricing and ROI expectations.</div>
            </div>
            """, unsafe_allow_html=True)

            with st.expander("🛠️ View Detected Software & Tools (Wappalyzer Profile)"):
                st.write(f"• **Competitor Video Widget:** `{score_res.details.get('shopscope_competitor', 'None detected')}`")
                st.write(f"• **Storefront Review Engine:** `{score_res.details.get('shopscope_reviews', 'None detected')}`")
                st.write(f"• **Analytics / Session Recorder:** `{score_res.details.get('shopscope_cro', 'None detected')}`")
                st.write(f"• **Email / SMS Marketing:** `{score_res.details.get('shopscope_email', 'None detected')}`")
                st.write(f"• **Marketing Pixels Active:** `{score_res.details.get('shopscope_pixels', 'None detected')}`")

        with in_col2:
            st.markdown("#### 🎯 Executive Strategy & Pitch Positioning")
            
            # Setup Strategy Options first
            reviews_tech = score_res.details.get('shopscope_reviews', 'None')
            competitor_tech = score_res.details.get('shopscope_competitor', 'None')
            
            ranked_strategies = []
            if "Staffing" in biz_type or "Services" in biz_type:
                ranked_strategies.append({
                    "rank": 1,
                    "confidence": "Strategic Fit",
                    "id": "b2b_talent_client_conversion",
                    "title": "Video Candidate & Client Testimonial Feeds",
                    "gap": "Static web pages lose high-intent corporate clients and top talent candidates.",
                    "solution": "Pitch Zeacon interactive video widgets for candidate stories and client case study reels.",
                    "impact": "8% to 12% lift in candidate completions and client inquiry conversion."
                })
                ranked_strategies.append({
                    "rank": 2,
                    "confidence": "High Opportunity",
                    "id": "b2b_cac_reduction",
                    "title": "Paid Ad & Campaign CAC Optimization",
                    "gap": "Running video ad campaigns driving traffic to static lead forms.",
                    "solution": "Map social video ad creatives directly to application and inquiry portals.",
                    "impact": "Lower Customer Acquisition Cost (CAC) and increase conversion."
                })
            elif "Automotive" in biz_type:
                ranked_strategies.append({
                    "rank": 1,
                    "confidence": "Strategic Fit",
                    "id": "auto_vehicle_tours",
                    "title": "Interactive Vehicle Walkthrough Reels",
                    "gap": "Buyers want video walkthroughs before visiting the showroom.",
                    "solution": "Embed floating Zeacon video players on vehicle inventory pages.",
                    "impact": "Increase test drive bookings and showroom inquiries."
                })
            elif "Hospitality" in biz_type:
                ranked_strategies.append({
                    "rank": 1,
                    "confidence": "Strategic Fit",
                    "id": "dining_experience_reels",
                    "title": "Dining Experience & Atmosphere Video Reels",
                    "gap": "Text menus fail to convey the dining experience compared to video reels.",
                    "solution": "Embed interactive video reels showing food preparation, atmosphere, and private dining.",
                    "impact": "Accelerate online table reservations and private event bookings."
                })
            elif competitor_tech != 'None':
                ranked_strategies.append({
                    "rank": 1,
                    "confidence": "Competitor Switch",
                    "id": "competitive_displacement",
                    "title": f"Competitor Displacement (Displace {competitor_tech})",
                    "gap": f"Currently uses {competitor_tech} static widgets.",
                    "solution": f"Pitch displacing {competitor_tech} with Zeacon's dynamic AI recommendation engine.",
                    "impact": "25% average lift in AOV compared to static widgets."
                })

            if not ranked_strategies:
                ranked_strategies.append({
                    "rank": 1,
                    "confidence": "Top Strategic Angle",
                    "id": "onsite_video_uplift",
                    "title": "Social-to-Website Video Monetization",
                    "gap": "Rich social video content exists, but website lacks interactive video widgets.",
                    "solution": "Repurpose Instagram/Facebook reels directly into floating website player widgets.",
                    "impact": "Up to 4x increase in time-on-site and 8-12% online sales lift."
                })

            if not st.session_state.get('selected_strategy_angle'):
                st.session_state['selected_strategy_angle'] = ranked_strategies[0]['id']
                
            active_angle = st.session_state['selected_strategy_angle']
            active_strat_obj = next((s for s in ranked_strategies if s['id'] == active_angle), ranked_strategies[0])

            # Executive CRO Strategy Brief
            generator = OutreachGenerator(
                provider=model_provider,
                anthropic_api_key=anthropic_key,
                gemini_api_key=gemini_key
            )
            contacts_list = st.session_state.get('current_contacts', [])
            target_contact_brief = contacts_list[st.session_state.get('active_contact_idx', 0)] if contacts_list else Contact(name="Executive Leader", title="CMO / VP Growth", email=f"info@{domain}")
            
            brief_key = f"exec_brief_{domain}_{target_contact_brief.name}_{active_angle}"
            if brief_key not in st.session_state:
                with st.spinner("Synthesizing Executive CRO Takeaways..."):
                    if hasattr(generator, 'generate_executive_brief'):
                        st.session_state[brief_key] = generator.generate_executive_brief(score_res, target_contact_brief)
                    else:
                        st.session_state[brief_key] = f"1. 💡 **Strategic Opportunity**: Repurpose active social video assets into on-site interactive feeds to capture 8-12% higher conversion.\n2. 🛠️ **Tech Stack Ecosystem**: Integrates natively with zero script bloat.\n3. 🎯 **Consultative Pitch Angle**: Position Zeacon to lower CAC and convert static storefront visitors."
            
            exec_brief_text = st.session_state[brief_key]
            exec_brief_html = exec_brief_text.replace('\n', '<br/>')

            # Render ONE Clean Consolidated Executive Briefing Card
            card_html = (
                f"<div style='background:#ffffff; border:1px solid #cbd5e1; border-left:5px solid #e11d48; border-radius:10px; padding:1.25rem; margin-bottom:1rem; box-shadow:0 1px 3px rgba(0,0,0,0.05);'>"
                f"<div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:0.75rem;'>"
                f"<span style='font-size:1.05rem; font-weight:800; color:#0f172a;'>🥇 {active_strat_obj['title']}</span>"
                f"<span style='background:#e11d48; color:white; font-size:0.7rem; font-weight:700; padding:3px 9px; border-radius:12px;'>{active_strat_obj['confidence']}</span>"
                f"</div>"
                f"<div style='background:#f8fafc; border-radius:8px; padding:0.85rem 1rem; margin-bottom:0.75rem; border:1px solid #e2e8f0;'>"
                f"<div style='font-weight:700; font-size:0.8rem; color:#475569; margin-bottom:0.4rem;'>👔 CRO EXECUTIVE BRIEFING</div>"
                f"<div style='font-size:0.83rem; color:#334155; line-height:1.6;'>{exec_brief_html}</div>"
                f"</div>"
                f"<div style='background:#ecfdf5; border:1px solid #a7f3d0; border-radius:6px; padding:0.6rem 0.85rem; font-size:0.82rem; color:#065f46; font-weight:600;'>"
                f"📈 Projected Business Impact: <span style='font-weight:700;'>{active_strat_obj['impact']}</span>"
                f"</div>"
                f"</div>"
            )
            st.markdown(card_html, unsafe_allow_html=True)

            if len(ranked_strategies) > 1:
                st.markdown("##### 🔄 Alternate Strategic Angles (1-Click Pivot)")
                for alt_s in ranked_strategies:
                    if alt_s['id'] != active_angle:
                        with st.expander(f"Option #{alt_s['rank']}: {alt_s['title']} ({alt_s['confidence']})"):
                            st.write(f"**Gap:** {alt_s['gap']}")
                            st.write(f"**Zeacon Solution:** {alt_s['solution']}")
                            st.write(f"**Impact:** {alt_s['impact']}")
                            if st.button(f"🎯 Pivot Email Draft to Option #{alt_s['rank']}", key=f"pivot_btn_{alt_s['id']}"):
                                st.session_state['selected_strategy_angle'] = alt_s['id']
                                if 'current_draft' in st.session_state:
                                    del st.session_state['current_draft']
                                st.toast(f"Pivoted email strategy to Option #{alt_s['rank']}!")
                                st.rerun()

            strat_col1, strat_col2 = st.columns(2)
            with strat_col1:
                if st.button("👍 Approve Strategy Angle", key="btn_strat_like"):
                    db.log_strategy_feedback(domain, active_angle, True, f"Approved angle: {active_strat_obj['title']}")
                    st.toast("Tactic approved! Strategy logged.")
            with strat_col2:
                if st.button("👎 Recalibrate Tactic", key="btn_strat_dislike"):
                    st.session_state['show_strat_critique_box'] = True
                    
            if st.session_state.get('show_strat_critique_box', False):
                strat_critique = st.text_input("What opportunity should we focus on instead?")
                if st.button("Submit Strategy Calibration"):
                    db.log_strategy_feedback(domain, active_angle, False, strat_critique)
                    st.toast("Strategy feedback logged! Model calibrating.")
                    st.session_state['show_strat_critique_box'] = False
                    if 'current_draft' in st.session_state:
                        del st.session_state['current_draft']
                    st.rerun()

        st.markdown("---")
        
        c_col1, c_col2 = st.columns([1, 1.2])
        
        with c_col1:
            st.markdown("#### Enriched Decision-Makers")
            st.write(f"Found Corporate Executives for **{biz_type}**:")
            
            active_idx = st.session_state.get('active_contact_idx', 0)
            for i, c in enumerate(contacts):
                btn_label = f"{c.name} - {c.title}"
                if st.button(btn_label, key=f"contact_btn_{i}", type="secondary" if i != active_idx else "primary"):
                    st.session_state['active_contact_idx'] = i
                    if 'current_draft' in st.session_state:
                        del st.session_state['current_draft']
                    st.rerun()
            
            active_idx = st.session_state.get('active_contact_idx', 0)
            if active_idx >= len(contacts):
                active_idx = 0
                st.session_state['active_contact_idx'] = 0
                
            target_contact = contacts[active_idx]
            
            st.markdown("##### Selected Contact Details")
            
            # Determine verification badge based on source
            source = getattr(target_contact, 'source', 'unknown') or 'unknown'
            if source == "apollo_verified":
                badge_html = '<span style="background:#059669; color:white; padding:2px 8px; border-radius:4px; font-size:0.7rem; font-weight:700; margin-left:8px;">✓ APOLLO VERIFIED</span>'
                email_badge = '<span style="color:#059669; font-size:0.75rem; font-weight:600;"> (verified)</span>'
            elif source == "hunter_verified":
                badge_html = '<span style="background:#0d9488; color:white; padding:2px 8px; border-radius:4px; font-size:0.7rem; font-weight:700; margin-left:8px;">✓ HUNTER VERIFIED</span>'
                email_badge = '<span style="color:#0d9488; font-size:0.75rem; font-weight:600;"> (verified email)</span>'
            elif source == "verified_vault":
                badge_html = '<span style="background:#2563eb; color:white; padding:2px 8px; border-radius:4px; font-size:0.7rem; font-weight:700; margin-left:8px;">✓ HAND VERIFIED</span>'
                email_badge = '<span style="color:#d97706; font-size:0.75rem;"> (estimated)</span>'
            elif source == "gemini_unverified":
                badge_html = '<span style="background:#d97706; color:white; padding:2px 8px; border-radius:4px; font-size:0.7rem; font-weight:700; margin-left:8px;">⚠ AI GENERATED</span>'
                email_badge = '<span style="color:#dc2626; font-size:0.75rem;"> (unverified)</span>'
            else:
                badge_html = '<span style="background:#94a3b8; color:white; padding:2px 8px; border-radius:4px; font-size:0.7rem; font-weight:700; margin-left:8px;">PLACEHOLDER</span>'
                email_badge = '<span style="color:#dc2626; font-size:0.75rem;"> (placeholder)</span>'

            if target_contact.linkedin and 'linkedin.com/in/' in target_contact.linkedin.lower():
                li_url = target_contact.linkedin.strip()
                li_label = f"View {target_contact.name} on LinkedIn"
            else:
                g_query = urllib.parse.quote(f"site:linkedin.com/in/ {target_contact.name} {domain}")
                li_url = f"https://www.google.com/search?q={g_query}"
                li_label = f"Find {target_contact.name} on LinkedIn (via Google)"
            
            li_html = f'<a href="{li_url}" target="_blank" style="color:#0077b5; font-weight:600; text-decoration:none;">{li_label} ↗</a>'
            
            st.markdown(f"""
            <div style='background:#ffffff; border:1px solid #e2e8f0; border-radius:10px; padding:1.1rem 1.3rem; margin-bottom:0.75rem;'>
                <div style='font-size:1.1rem; font-weight:700; color:#0f172a; margin-bottom:0.35rem;'>{target_contact.name}{badge_html}</div>
                <div style='font-size:0.9rem; color:#475569; margin-bottom:0.6rem;'>{target_contact.title}</div>
                <div style='font-size:0.85rem; color:#334155; margin-bottom:0.3rem;'>📧 {target_contact.email}{email_badge}</div>
                <div style='font-size:0.85rem; color:#334155;'>💼 {li_html}</div>
            </div>
            """, unsafe_allow_html=True)

        with c_col2:
            st.markdown("#### Dynamic Outreach Generation")
            
            vault = AmmoVault()
            best_ammo = vault.select_best_ammo(score_res)
            st.markdown(f"**Auto-Selected Case Study:** *{best_ammo.get('title')}* (**{best_ammo.get('metric')}**)")
            
            tweak_input = st.text_input("💡 Tweak Instructions (e.g., 'Make the tone more casual')", value=st.session_state.get('custom_tweak_input', ''))
            
            generator = OutreachGenerator(
                provider=model_provider,
                anthropic_api_key=anthropic_key,
                gemini_api_key=gemini_key
            )
            
            if tweak_input != st.session_state.get('custom_tweak_input', ''):
                st.session_state['custom_tweak_input'] = tweak_input
                if 'current_draft' in st.session_state:
                    del st.session_state['current_draft']
            
            if st.button("Generate / Tweak Draft", type="primary"):
                st.session_state['custom_tweak_input'] = tweak_input
                with st.spinner("Regenerating copy with tweak instructions..."):
                    draft = generator.generate_draft(score_res, target_contact, best_ammo, user_tweak=tweak_input)
                    st.session_state['current_draft'] = draft
            
            if 'current_draft' not in st.session_state:
                st.session_state['current_draft'] = generator.generate_draft(score_res, target_contact, best_ammo, user_tweak=tweak_input)
                
            active_draft = st.session_state['current_draft']
            st.markdown("##### 💼 LinkedIn Connection Invite Note (Kris Naidu, CEO Intro)")
            ln_note = getattr(active_draft, 'linkedin_note', '')
            if not ln_note:
                first_name = target_contact.name.split()[0] if target_contact.name else "there"
                clean_d = domain.split('.')[0].capitalize()
                ln_note = f"Hi {first_name}, I'm Kris Naidu, CEO of Zeacon. Noticed {clean_d}'s website growth—we help brands turn social video into on-site revenue (avg +25% lift) with zero site speed impact. Would love to connect and share a quick video ROI audit for {clean_d}!"

            char_len = len(ln_note)
            char_badge = f"<span style='background:#ecfdf5; color:#059669; border:1px solid #a7f3d0; padding:2px 8px; border-radius:4px; font-size:0.75rem; font-weight:700;'>{char_len} / 300 chars (Fits LinkedIn Limit)</span>" if char_len <= 300 else f"<span style='background:#fef2f2; color:#dc2626; border:1px solid #fecaca; padding:2px 8px; border-radius:4px; font-size:0.75rem; font-weight:700;'>{char_len} / 300 chars (Too Long)</span>"

            st.markdown(f"<div style='font-size:0.8rem; color:#475569; margin-bottom:0.35rem;'>Personalized invitation note for Kris to send on LinkedIn {char_badge}:</div>", unsafe_allow_html=True)
            st.text_area("LinkedIn Connection Note (Copy & Paste)", value=ln_note, height=95, key="linkedin_note_display")

            st.markdown("##### ✉️ Cold Email Draft")
            st.text_input("Outreach Subject Line", value=active_draft.subject, key="subject_display")
            draft_body_area = st.text_area("Email Body Draft", value=active_draft.body, height=320, key="body_display")
            
            st.markdown("##### 🚀 Outreach & Sequence Actions")
            act_col1, act_col2 = st.columns([1.2, 1])
            with act_col1:
                channel_choice = st.selectbox("Sent Channel", ["Email", "LinkedIn Message", "LinkedIn Invite Note"], key="sel_sent_channel")
            with act_col2:
                enroll_btn = st.button("🚀 Mark Sent & Enroll in Sequence", type="primary", use_container_width=True, key="btn_enroll_seq")

            if enroll_btn:
                sent_body = ln_note if "LinkedIn Invite" in channel_choice else draft_body_area
                seq_id = db.start_sequence(
                    domain=domain,
                    contact_name=target_contact.name,
                    contact_email=target_contact.email,
                    contact_title=target_contact.title,
                    contact_linkedin=target_contact.linkedin or "",
                    channel=channel_choice,
                    initial_subject=active_draft.subject,
                    initial_body=sent_body
                )
                db.log_outreach(domain, target_contact.name, target_contact.title, active_draft.subject, sent_body)
                st.success(f"🎉 Enrolled {target_contact.name} ({clean_domain}) into Follow-Up Sequence! Next follow-up scheduled in 3 days.")
                st.balloons()

            log_btn = st.button("📋 Log Draft Only (No Sequence)")
            if log_btn:
                log_id = db.log_outreach(domain, target_contact.name, target_contact.title, active_draft.subject, draft_body_area)
                st.session_state['last_log_id'] = log_id
                st.success("Draft saved and logged to database! Copy using Ctrl+A / Ctrl+C.")

            st.markdown("##### Feedback Loop")
            feedback_col1, feedback_col2 = st.columns(2)
            with feedback_col1:
                liked = st.button("👍 Good Draft", key="btn_like")
                if liked:
                    log_id = db.log_outreach(domain, target_contact.name, target_contact.title, active_draft.subject, draft_body_area)
                    db.update_outreach_feedback(log_id, True, "Keep tone professional and brief.")
                    st.toast("Marked as Liked! System adjusted.")
            with feedback_col2:
                disliked = st.button("👎 Needs Improvement", key="btn_dislike")
                if disliked:
                    st.session_state['show_critique_box'] = True
            
            if st.session_state.get('show_critique_box', False):
                critique = st.text_input("Tell us what went wrong")
                if st.button("Submit Critique & Recalibrate"):
                    log_id = db.log_outreach(domain, target_contact.name, target_contact.title, active_draft.subject, draft_body_area)
                    db.update_outreach_feedback(log_id, False, critique)
                    st.toast("Feedback logged! Model prompt alignment recalibrated.")
                    st.session_state['show_critique_box'] = False
                    
                    if 'current_draft' in st.session_state:
                        del st.session_state['current_draft']
                    st.rerun()

with tab_sequences:
    st.subheader("📅 Sales Sequences & Follow-Up Command Center")
    st.markdown("<p style='color:#475569; font-size:0.95rem; margin-bottom:1rem;'>Manage active multi-touch cadences. Generate contextual follow-up copy, track reply status, and never let warm prospects slip through the cracks.</p>", unsafe_allow_html=True)
    
    all_sequences = db.get_sequences()
    from datetime import datetime
    now_dt = datetime.now()
    
    due_sequences = []
    active_sequences = []
    replied_sequences = []
    completed_sequences = []
    
    for s in all_sequences:
        st_status = s.get('status', 'ACTIVE')
        if st_status == 'REPLIED':
            replied_sequences.append(s)
        elif st_status == 'COMPLETED':
            completed_sequences.append(s)
        elif st_status == 'ACTIVE':
            active_sequences.append(s)
            next_act = s.get('next_action_date')
            if next_act:
                try:
                    act_dt = datetime.strptime(next_act.split('.')[0], '%Y-%m-%d %H:%M:%S')
                    if act_dt <= now_dt:
                        due_sequences.append(s)
                except Exception:
                    pass

    sq_c1, sq_c2, sq_c3, sq_c4 = st.columns(4)
    with sq_c1:
        st.markdown(f"<div class='metric-card'><div class='metric-title'>🚨 Action Due Now</div><div class='metric-value' style='color:#dc2626;'>{len(due_sequences)}</div><div style='color:#64748b; font-size:0.8rem;'>Follow-ups due today</div></div>", unsafe_allow_html=True)
    with sq_c2:
        st.markdown(f"<div class='metric-card'><div class='metric-title'>⏳ Active Cadences</div><div class='metric-value' style='color:#0284c7;'>{len(active_sequences)}</div><div style='color:#64748b; font-size:0.8rem;'>In-progress sequences</div></div>", unsafe_allow_html=True)
    with sq_c3:
        st.markdown(f"<div class='metric-card'><div class='metric-title'>🎉 Replied / Booked</div><div class='metric-value' style='color:#059669;'>{len(replied_sequences)}</div><div style='color:#64748b; font-size:0.8rem;'>Positive responses</div></div>", unsafe_allow_html=True)
    with sq_c4:
        st.markdown(f"<div class='metric-card'><div class='metric-title'>✅ Completed</div><div class='metric-value' style='color:#475569;'>{len(completed_sequences)}</div><div style='color:#64748b; font-size:0.8rem;'>Finished 4-touch cycle</div></div>", unsafe_allow_html=True)

    st.markdown("---")
    
    seq_filter = st.radio("Filter Sequence Queue:", ["🚨 Due for Action", "⏳ All Active", "🎉 Replied / Won", "📋 All Prospects"], horizontal=True)
    
    display_list = []
    if seq_filter == "🚨 Due for Action":
        display_list = due_sequences
    elif seq_filter == "⏳ All Active":
        display_list = active_sequences
    elif seq_filter == "🎉 Replied / Won":
        display_list = replied_sequences
    else:
        display_list = all_sequences

    if not display_list:
        st.info("No prospect sequences match this filter right now. Run a search in the Prospect Analyzer and click '🚀 Mark Sent & Enroll in Sequence' to get started!")
    else:
        seq_gen = OutreachGenerator(provider=model_provider, anthropic_api_key=anthropic_key, gemini_api_key=gemini_key)
        for s in display_list:
            s_id = s['id']
            domain_name = s['domain']
            contact_name = s.get('contact_name', 'Executive')
            contact_title = s.get('contact_title', 'Decision Maker')
            step = s.get('current_step', 1)
            status = s.get('status', 'ACTIVE')
            last_touch = s.get('last_touch_date', '')
            next_action = s.get('next_action_date', 'Completed')
            history = s.get('history', [])
            
            step_labels = {1: "Touch 1 (Initial Pitch)", 2: "Touch 2 (Social Proof Bump)", 3: "Touch 3 (Zero-Speed Handle)", 4: "Touch 4 (Executive Breakup)"}
            next_step_label = step_labels.get(step + 1, "Completed")
            
            is_due = False
            if next_action and next_action != 'Completed':
                try:
                    act_dt = datetime.strptime(next_action.split('.')[0], '%Y-%m-%d %H:%M:%S')
                    is_due = act_dt <= now_dt
                except Exception:
                    pass

            due_tag = "🔴 **DUE TODAY**" if is_due and status == 'ACTIVE' else f"Next: {next_action.split(' ')[0] if next_action else 'None'}"
            expander_title = f"{'🚨 ' if is_due and status == 'ACTIVE' else '👤 '}{contact_name} @ {domain_name} — Step {step}/4 ({status}) | {due_tag}"
            
            with st.expander(expander_title, expanded=(is_due and status == 'ACTIVE')):
                col_i1, col_i2 = st.columns([1, 1])
                with col_i1:
                    st.markdown(f"**Contact:** `{contact_name}` ({contact_title})")
                    st.markdown(f"**Domain:** `{domain_name}` | **Email:** `{s.get('contact_email', 'None')}`")
                    if s.get('contact_linkedin'):
                        st.markdown(f"[🔗 Open LinkedIn Profile]({s.get('contact_linkedin')})")
                with col_i2:
                    st.markdown(f"**Current Cadence Progress:** `Step {step} of 4` ({step_labels.get(step, 'Initial')})")
                    st.markdown(f"**Status:** `{status}` | **Last Contact:** `{last_touch.split(' ')[0] if last_touch else 'N/A'}`")
                    st.markdown(f"**Scheduled Next Touch:** `{next_action.split(' ')[0] if next_action else 'N/A'}`")

                # Sequence Touch History
                if history:
                    st.markdown("##### 📜 Previous Touch History")
                    for h in history:
                        st.markdown(f"""
                        <div style='background:#f8fafc; border-left:3px solid #0284c7; padding:0.5rem 0.8rem; margin-bottom:0.4rem; border-radius:0 6px 6px 0; font-size:0.8rem;'>
                            <strong>Touch {h.get('step')} ({h.get('channel')})</strong> • <em>{h.get('sent_at')}</em><br/>
                            <span style='color:#475569;'><strong>Subject:</strong> {h.get('subject', 'N/A')}</span><br/>
                            <div style='color:#334155; margin-top:0.2rem; white-space:pre-wrap;'>{h.get('body', '')[:200]}...</div>
                        </div>
                        """, unsafe_allow_html=True)

                # Next Touch Generator (If Active and Step < 4)
                if status == 'ACTIVE' and step < 4:
                    next_step = step + 1
                    st.markdown(f"##### ✍️ AI-Generated {step_labels.get(next_step, 'Follow-Up')}")
                    followup_drafts = seq_gen.generate_followup_draft(s, step=next_step)
                    
                    fu_tab_email, fu_tab_li = st.tabs(["✉️ Follow-Up Email", "💼 LinkedIn Follow-Up"])
                    with fu_tab_email:
                        st.text_input("Subject Line", value=followup_drafts['email_subject'], key=f"fu_subj_{s_id}_{next_step}")
                        fu_email_body = st.text_area("Email Copy (1-Click Copy)", value=followup_drafts['email_body'], height=200, key=f"fu_body_{s_id}_{next_step}")
                    with fu_tab_li:
                        fu_li_msg = st.text_area("LinkedIn Message", value=followup_drafts['linkedin_message'], height=100, key=f"fu_li_{s_id}_{next_step}")

                    act_c1, act_c2, act_c3 = st.columns([1.5, 1.2, 1])
                    with act_c1:
                        fu_channel = st.selectbox("Sent via", ["Email", "LinkedIn Message"], key=f"fu_chan_{s_id}")
                        if st.button(f"✅ Mark Touch {next_step} Sent (+Advance)", type="primary", key=f"btn_adv_{s_id}"):
                            body_to_save = fu_li_msg if "LinkedIn" in fu_channel else fu_email_body
                            db.advance_sequence(s_id, fu_channel, followup_drafts['email_subject'], body_to_save)
                            st.toast("Sequence advanced! Next step scheduled.")
                            st.rerun()
                    with act_c2:
                        if st.button("🎉 Mark Replied / Booked", key=f"btn_rep_{s_id}"):
                            db.update_sequence_status(s_id, 'REPLIED')
                            st.toast("Prospect marked as REPLIED! Congratulations.")
                            st.rerun()
                    with act_c3:
                        if st.button("🗑️ Delete", key=f"btn_del_{s_id}"):
                            db.delete_sequence(s_id)
                            st.toast("Sequence deleted.")
                            st.rerun()
                else:
                    st.markdown("##### Actions")
                    r_c1, r_c2 = st.columns(2)
                    with r_c1:
                        if status == 'REPLIED':
                            st.success("🎉 Meeting / Conversation in progress!")
                        else:
                            st.info("Sequence cycle completed.")
                    with r_c2:
                        if st.button("🗑️ Remove Sequence", key=f"btn_del_done_{s_id}"):
                            db.delete_sequence(s_id)
                            st.rerun()
        df = pd.DataFrame(prospects)
        st.dataframe(df[['domain', 'total_score', 'video_ads_score', 'traffic_score', 'onsite_video_score', 'cart_score', 'timestamp']], use_container_width=True)
        
        st.markdown("#### Generated Outreach History & Feedback Tracker")
        logs = db.get_outreach_logs()
        if logs:
            st.dataframe(pd.DataFrame(logs)[['domain', 'contact_name', 'persona', 'liked', 'feedback', 'timestamp']], use_container_width=True)
            
        st.markdown("#### Strategy Tactic Log & Feedback Tracker")
        s_logs = db.get_strategy_logs()
        if s_logs:
            st.dataframe(pd.DataFrame(s_logs)[['domain', 'strategy_angle', 'liked', 'critique', 'timestamp']], use_container_width=True)
    else:
        st.info("No queries processed yet.")

with tab_ammo:
    st.subheader("Proof Points & Winning Outreach Vault")
    
    st.markdown("#### 📥 Proven Outreach Vault (Train the AI with Real Closed Deals)")
    st.write("Upload or view real emails that have successfully closed business or generated high response rates. The AI emulates these exact writing patterns.")
    
    winning_emails = db.get_winning_outreach()
    if winning_emails:
        for w in winning_emails:
            with st.expander(f"⭐ {w['title']}"):
                st.markdown(f"**Email Body:**\n\n```\n{w['email_body']}\n```")
                if w.get('notes'):
                    st.write(f"**Key Selling Points:** {w['notes']}")
                    
    with st.expander("➕ Add New Winning Outreach Example"):
        with st.form("add_winning_form"):
            w_title = st.text_input("Example Name (e.g. 'Kris Closed Deal Email - D2C Focus')")
            w_body = st.text_area("Paste Winning Email Body", height=150)
            w_notes = st.text_input("Notes / Why It Worked (e.g. 'Mentions 8-12% sales lift and CAC reduction')")
            
            submit_winning = st.form_submit_button("Save Winning Template & Train AI")
            if submit_winning and w_title and w_body:
                db.add_winning_outreach(w_title, w_body, w_notes)
                st.success(f"Winning template '{w_title}' added! The AI will now emulate this prose.")
                st.rerun()

    st.markdown("---")

    st.markdown("#### 📖 Case Studies & Verified Metrics")
    studies = db.get_case_studies()
    if studies:
        for s in studies:
            with st.expander(f"📖 {s['title']} ({s['metric']})"):
                st.write(f"**Focus Area:** {s['focus']}")
                st.write(f"**Description:** {s['description']}")
                
    st.markdown("##### Add New Proof Point")
    with st.form("add_ammo_form"):
        title_in = st.text_input("Title")
        metric_in = st.text_input("Metric")
        focus_in = st.text_input("Focus Area")
        desc_in = st.text_area("Detailed Description")
        
        submit_ammo = st.form_submit_button("Save Case Study")
        if submit_ammo and title_in and metric_in:
            db.add_case_study(title_in, metric_in, focus_in, desc_in)
            st.success(f"Case study '{title_in}' added to SQLite Vault!")
            st.rerun()
