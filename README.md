# AI LinkedIn Executive Roles & Hiring Manager Discovery System

An autonomous AI-powered system that accepts **any candidate resume** (Data Science, AI/ML, Product Management, Engineering, etc.), calculates total Years of Experience (YoE), detects career tracks, crawls LinkedIn for live **Similar** and **Higher** career opportunities across Indian and global cities, and dynamically discovers the **verified LinkedIn profile URLs of hiring managers and executive decision-makers** (VP of Data Science, Head of AI, CPO, VP Product, CTO).

---

## 🌟 Core Capabilities

### 1. 🔍 100% Dynamic Hiring Manager & Executive Discovery
* **Zero Hardcoded Names**: Discovers hiring managers in real time using live LinkedIn search across **any company** in the world (startups, unicorns, MNCs).
* **Job Description (JD) Reporting-Line Extraction**: Parses the actual job description text for reporting hierarchy phrases (e.g. *"Reports to VP of Product"*, *"Reporting to Director of Engineering"*, *"Working closely with Chief Technology Officer"*) to search for the exact reporting executive.
* **Seniority-Aware Target Mapping**:
  * Applying for Lead / Principal roles -> Finds **Director of Product / Head of AI / VP of Engineering**.
  * Applying for Director / VP roles -> Finds **Chief Product Officer (CPO) / CTO / Founder & CEO**.
* **Direct 1-Click LinkedIn Search Fallback**: If a company's leadership is private or search-limited, generates a direct pre-filtered LinkedIn People Directory link for that specific company and department.

### 2. 🤖 Universal Domain & Track Support (Data Science, Product, Engineering)
* **Automatic Track Detection**: Intelligently analyzes whether the resume belongs to **Data Science & AI**, **Product Management**, **Software Engineering**, or other domains.
* **Dynamic Seniority & Target Role Mapping**:
  * *For Data Science Leader (e.g., 11+ YoE)*:
    * 🚀 **Higher Roles**: Director of Data Science, Head of Data Science, Head of AI, VP of Data Science, VP of AI, Chief Data Scientist / CDO.
    * ⚡ **Similar Roles**: Lead Data Scientist, Principal Data Scientist, Staff Data Scientist, AI Architect.
  * *For Product Leader (e.g., 12+ YoE)*:
    * 🚀 **Higher Roles**: Director of Product, VP of Product, Head of Product, Chief Product Officer.
    * ⚡ **Similar Roles**: Group Product Manager, Principal Product Manager, Lead PM.
* **Editable Resume with One-Click Presets & File Upload**:
  * ⭐ *Preset 1*: Product Leadership (**Twisha Prasad**, 12+ YoE)
  * ⭐ *Preset 2*: Data Science & AI Leadership (**Dr. Aryan Sharma**, 11+ YoE)
  * ⭐ *Preset 3*: Senior Data Scientist (**Sneha Rao**, 6+ YoE)
  * ✍ *Preset 4*: Custom / Blank Resume (Upload `.txt`, `.pdf`, `.docx`, or paste freely).

### 3. 📅 Order by Date of Posting (Latest First by Default)
* **Automatic Date Extraction**: Parses both ISO `<time datetime="...">` tags and relative strings ("3 hours ago", "2 days ago", "1 week ago") into precise timestamps.
* **Newest Postings First**: When search results arrive, they are automatically ordered so the freshest job postings appear at the top.
* **Sort Switcher**: Toggle easily between `📅 Date Posted (Latest First)` and `🎯 Match Score (Highest First)`.

### 4. 🎯 Rigorous Resume vs Actual JD Match Scoring (No Arbitrary 85%)
* Scores are calculated mathematically by comparing the **Candidate Resume** directly against the **LinkedIn Job Description (JD)**:
  1. **TF-IDF Semantic Cosine Similarity (35 pts)**: Unigram & bigram vector cosine alignment between Resume and JD.
  2. **YoE Delta Fit (25 pts)**: Automatically parses required YoE from the JD (e.g., `10+ years`, `8-12 years`) and checks against candidate's actual YoE.
  3. **Hard Skills & Tech Stack Overlap (30 pts)**: Identifies verified **Matching Skills** (e.g., *PyTorch*, *Transformers*, *LLMs*, *MLOps*) and flags **Missing / Desired Skills** in the JD.
  4. **Leadership Scope (10 pts)**: Analyzes team leadership requirements and people management background.
* Exposes nuanced, realistic scores (e.g., 63%, 69%, 74%, 88%, 94%).

### 5. ♾️ Unlimited Pagination & Deep Crawling
* Real pagination bar (`[Prev Page] Page X [Next Page]`) with customizable page sizes (6, 10, 15).
* Feeds pagination offsets directly to LinkedIn's live guest API to explore jobs as deep as needed.

---

## ☁️ Permanent 24/7 Cloud Hosting (No Local Script Required)

You can host this application permanently on the cloud for free without keeping your computer running.

### Option A: Render.com (Recommended - 100% Free)
1. Push this project to your GitHub repository:
   ```bash
   git init
   git add .
   git commit -m "feat: linkedin hiring manager finder"
   git remote add origin https://github.com/<your-username>/linkedin-career-finder.git
   git push -u origin main
   ```
2. Go to **[Render.com](https://render.com)** (sign in with your GitHub account).
3. Click **New +** -> **Web Service**.
4. Select your `linkedin-career-finder` repository.
5. Set:
   * **Runtime**: `Python`
   * **Build Command**: `pip install -r requirements.txt`
   * **Start Command**: `uvicorn app:app --host 0.0.0.0 --port $PORT`
   * **Instance Type**: `Free`
6. Click **Deploy Web Service**.
7. Render will provide a permanent public HTTPS URL (e.g., `https://linkedin-career-finder.onrender.com`) that stays live 24/7 on your mobile phone or any PC!

### Option B: Docker / Any Cloud Server (AWS, GCP, DigitalOcean)
Use the included `Dockerfile`:
```bash
docker build -t linkedin-finder .
docker run -p 8000:8000 -e PORT=8000 linkedin-finder
```

---

## 💻 Local Quickstart

### 1. Interactive Web Dashboard
```bash
python run.py --web
```
Open **`http://127.0.0.1:8000`** in your browser.

### 2. Command Line Interface (CLI)
```bash
# Search for Data Science Roles for Dr. Aryan Sharma (Higher roles only)
python cli.py --resume sample_resumes/aryan_sharma_data_science_lead.txt --level higher --limit 5

# Search for Product Roles for Twisha Prasad
python cli.py --resume sample_resumes/twisha_prasad.txt --level all --sort date --limit 6
```

### 3. Run Automated Tests
```bash
python test_system.py
```
