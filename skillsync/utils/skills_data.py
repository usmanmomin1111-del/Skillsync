"""
Domain metadata and realistic AICTE & PM Internship Scheme postings for SkillSync.

Each domain defines:
- skills: reference skill-set used for keyword matching and skill-gap detection
- description: job role reference text for Sentence-BERT semantic similarity
- internships: authentic AICTE Portal, PM Internship Scheme, and TULIP postings
"""

DOMAINS = {
    "Web Development": {
        "skills": [
            "HTML", "CSS", "JavaScript", "React", "Node.js", "Express",
            "REST API", "Git", "Responsive Design", "SQL", "MongoDB", "Flask"
        ],
        "description": (
            "Build and maintain responsive web applications using HTML, CSS, "
            "JavaScript and modern frameworks, integrate REST APIs and "
            "databases, and collaborate using Git-based workflows."
        ),
        "internships": [
            {
                "id": "aicte-web-cisco",
                "title": "Full Stack Web Developer Virtual Intern",
                "company": "CISCO Networking Academy & AICTE",
                "portal_type": "AICTE Official Partner",
                "portal_url": "https://internship.aicte-india.org/",
                "location": "Virtual / Work from Home",
                "stipend": "₹10,000 / month",
                "duration": "2 Months",
                "openings": "300 Openings",
                "skills_required": ["HTML", "CSS", "JavaScript", "React", "Git"],
                "description": "Develop modern responsive web modules and collaborate on cloud-integrated full stack projects under the AICTE-CISCO virtual internship initiative."
            },
            {
                "id": "pmis-web-tcs",
                "title": "Web Application Developer Intern",
                "company": "Tata Consultancy Services (PM Internship Scheme)",
                "portal_type": "PM Internship Scheme (PMIS)",
                "portal_url": "https://pminternship.mca.gov.in/",
                "location": "Bengaluru / Pune (Hybrid)",
                "stipend": "₹5,000 (Govt) + ₹6,000 Corp Allowance",
                "duration": "3 Months",
                "openings": "120 Openings",
                "skills_required": ["HTML", "JavaScript", "REST API", "SQL", "Git"],
                "description": "Work on scalable client-facing web portals under India's flagship PM Internship Scheme in India's top 500 companies."
            },
            {
                "id": "tulip-web-smartcity",
                "title": "Smart City Citizen Portal Developer Intern",
                "company": "Ministry of Housing & Urban Affairs (TULIP)",
                "portal_type": "TULIP (MoHUA)",
                "portal_url": "https://internship.aicte-india.org/",
                "location": "Municipal Corporation / Hybrid",
                "stipend": "₹12,000 / month",
                "duration": "6 Months",
                "openings": "45 Openings",
                "skills_required": ["HTML", "CSS", "JavaScript", "Flask", "SQL"],
                "description": "Build citizen grievance and smart civic dashboards under The Urban Learning Internship Program (TULIP)."
            },
            {
                "id": "aicte-web-eduskills",
                "title": "Frontend & Cloud Application Intern",
                "company": "AWS Academy & EduSkills (AICTE)",
                "portal_type": "AICTE Official Partner",
                "portal_url": "https://internship.aicte-india.org/",
                "location": "Virtual / Remote",
                "stipend": "₹8,500 / month",
                "duration": "2 Months",
                "openings": "500 Openings",
                "skills_required": ["HTML", "CSS", "JavaScript", "React", "REST API"],
                "description": "Construct reactive user interfaces and serverless frontend components supported by AWS Academy on the AICTE portal."
            },
        ],
    },
    "AI / Machine Learning": {
        "skills": [
            "Python", "Machine Learning", "Deep Learning", "TensorFlow", "PyTorch",
            "NLP", "Sentence-BERT", "Scikit-learn", "Pandas", "NumPy", "Data Preprocessing"
        ],
        "description": (
            "Design and train machine learning and NLP models using Python, "
            "apply embedding-based semantic similarity, and evaluate model "
            "performance on real-world datasets."
        ),
        "internships": [
            {
                "id": "aicte-ai-ibm",
                "title": "AI & Machine Learning Virtual Intern",
                "company": "IBM SkillsBuild & AICTE",
                "portal_type": "AICTE Official Partner",
                "portal_url": "https://internship.aicte-india.org/",
                "location": "Virtual / Remote",
                "stipend": "₹12,000 / month",
                "duration": "2 Months",
                "openings": "400 Openings",
                "skills_required": ["Python", "Machine Learning", "Scikit-learn", "Pandas", "NumPy"],
                "description": "Build real-world predictive ML pipelines and classification algorithms mentored by IBM technical experts via AICTE."
            },
            {
                "id": "pmis-ai-lnt",
                "title": "Industrial AI & Computer Vision Intern",
                "company": "Larsen & Toubro (PM Internship Scheme)",
                "portal_type": "PM Internship Scheme (PMIS)",
                "portal_url": "https://pminternship.mca.gov.in/",
                "location": "Mumbai / Chennai",
                "stipend": "₹5,000 (Govt) + ₹8,000 Corp Allowance",
                "duration": "3 Months",
                "openings": "80 Openings",
                "skills_required": ["Python", "Deep Learning", "TensorFlow", "PyTorch"],
                "description": "Implement computer vision and anomaly detection models for smart manufacturing under the PM Internship Scheme."
            },
            {
                "id": "aicte-ai-google",
                "title": "Applied NLP & Generative AI Intern",
                "company": "Google Cloud & AICTE",
                "portal_type": "AICTE Official Partner",
                "portal_url": "https://internship.aicte-india.org/",
                "location": "Virtual / Remote",
                "stipend": "₹15,000 / month",
                "duration": "3 Months",
                "openings": "150 Openings",
                "skills_required": ["Python", "NLP", "Sentence-BERT", "Machine Learning", "Pandas"],
                "description": "Train semantic search systems, LLM prompts, and NLP classification models with Google Cloud AI technologies."
            },
            {
                "id": "tulip-ai-traffic",
                "title": "Smart Traffic & AI Surveillance Intern",
                "company": "Urban Development Directorate (TULIP)",
                "portal_type": "TULIP (MoHUA)",
                "portal_url": "https://internship.aicte-india.org/",
                "location": "New Delhi / Hybrid",
                "stipend": "₹10,000 / month",
                "duration": "4 Months",
                "openings": "35 Openings",
                "skills_required": ["Python", "Machine Learning", "Pandas", "Data Preprocessing"],
                "description": "Analyze vehicular mobility datasets and optimize traffic congestion algorithms for municipal smart city hubs."
            },
        ],
    },
    "Data Science": {
        "skills": [
            "Python", "SQL", "Pandas", "NumPy", "Data Visualization", "Power BI",
            "Statistics", "Machine Learning", "Excel", "Tableau"
        ],
        "description": (
            "Analyze structured and unstructured data, build dashboards and "
            "reports, and apply statistical and machine learning techniques "
            "to derive business insights."
        ),
        "internships": [
            {
                "id": "aicte-ds-ey",
                "title": "Data Analytics & Business Insights Intern",
                "company": "Ernst & Young (EY) & AICTE",
                "portal_type": "AICTE Official Partner",
                "portal_url": "https://internship.aicte-india.org/",
                "location": "Virtual / Remote",
                "stipend": "₹12,000 / month",
                "duration": "2 Months",
                "openings": "250 Openings",
                "skills_required": ["Python", "SQL", "Pandas", "Power BI", "Excel"],
                "description": "Process multi-source datasets, generate interactive Power BI executive dashboards, and extract business intelligence."
            },
            {
                "id": "pmis-ds-reliance",
                "title": "Enterprise Data Analytics Intern",
                "company": "Reliance Industries (PM Internship Scheme)",
                "portal_type": "PM Internship Scheme (PMIS)",
                "portal_url": "https://pminternship.mca.gov.in/",
                "location": "Navi Mumbai / Hybrid",
                "stipend": "₹5,000 (Govt) + ₹10,000 Allowance",
                "duration": "3 Months",
                "openings": "90 Openings",
                "skills_required": ["SQL", "Python", "Tableau", "Data Visualization", "Statistics"],
                "description": "Analyze customer retention and supply chain telemetry under India's top corporate cohort of the PM Internship Scheme."
            },
            {
                "id": "tulip-ds-urban",
                "title": "Urban Governance Data Analyst Intern",
                "company": "Smart Cities Mission (MoHUA - TULIP)",
                "portal_type": "TULIP (MoHUA)",
                "portal_url": "https://internship.aicte-india.org/",
                "location": "Pune Municipal Corp",
                "stipend": "₹10,000 / month",
                "duration": "6 Months",
                "openings": "25 Openings",
                "skills_required": ["Excel", "SQL", "Power BI", "Data Visualization"],
                "description": "Analyze municipal ward budgets, public health metrics, and infrastructure delivery datasets under TULIP."
            },
            {
                "id": "aicte-ds-alteryx",
                "title": "Automated Data Analytics Intern",
                "company": "Alteryx SparkED & AICTE",
                "portal_type": "AICTE Official Partner",
                "portal_url": "https://internship.aicte-india.org/",
                "location": "Virtual / Remote",
                "stipend": "₹8,500 / month",
                "duration": "2 Months",
                "openings": "350 Openings",
                "skills_required": ["Python", "Pandas", "Statistics", "Machine Learning"],
                "description": "Learn no-code/low-code data prep and predictive modeling through Alteryx SparkED's AICTE accredited program."
            },
        ],
    },
    "Software Engineering": {
        "skills": [
            "Java", "C++", "Python", "Data Structures", "Algorithms", "OOP",
            "Git", "SQL", "System Design", "Testing", "Flask", "Django"
        ],
        "description": (
            "Design, implement and test scalable software systems, apply "
            "data structures and algorithms, and work within version-controlled "
            "engineering teams."
        ),
        "internships": [
            {
                "id": "aicte-se-cisco",
                "title": "Software & Network Systems Engineering Intern",
                "company": "CISCO Networking Academy & AICTE",
                "portal_type": "AICTE Official Partner",
                "portal_url": "https://internship.aicte-india.org/",
                "location": "Virtual / Remote",
                "stipend": "₹12,000 / month",
                "duration": "2 Months",
                "openings": "300 Openings",
                "skills_required": ["Python", "C++", "Data Structures", "Algorithms", "Git"],
                "description": "Implement efficient algorithmic solutions, optimize system throughput, and write unit tests for distributed network tools."
            },
            {
                "id": "pmis-se-infosys",
                "title": "Software Engineering Trainee Intern",
                "company": "Infosys Springboard (PM Internship Scheme)",
                "portal_type": "PM Internship Scheme (PMIS)",
                "portal_url": "https://pminternship.mca.gov.in/",
                "location": "Bengaluru / Mysuru",
                "stipend": "₹5,000 (Govt) + ₹7,000 Allowance",
                "duration": "3 Months",
                "openings": "200 Openings",
                "skills_required": ["Java", "OOP", "SQL", "Git", "Testing"],
                "description": "Develop and test modular enterprise Java services under the PM Internship Scheme at Infosys development centers."
            },
            {
                "id": "tulip-se-nic",
                "title": "E-Governance Backend Engineering Intern",
                "company": "National Informatics Centre (NIC / AICTE)",
                "portal_type": "TULIP (MoHUA)",
                "portal_url": "https://internship.aicte-india.org/",
                "location": "New Delhi / Hybrid",
                "stipend": "₹10,000 / month",
                "duration": "6 Months",
                "openings": "60 Openings",
                "skills_required": ["Java", "SQL", "System Design", "Django"],
                "description": "Contribute to central digital governance APIs and microservices powering national portal initiatives."
            },
            {
                "id": "aicte-se-salesforce",
                "title": "Cloud Software Developer Intern",
                "company": "Salesforce & AICTE Virtual Internship",
                "portal_type": "AICTE Official Partner",
                "portal_url": "https://internship.aicte-india.org/",
                "location": "Virtual / Remote",
                "stipend": "₹14,000 / month",
                "duration": "3 Months",
                "openings": "400 Openings",
                "skills_required": ["Java", "OOP", "Data Structures", "Git", "REST API"],
                "description": "Build custom Apex enterprise logic, integrate asynchronous triggers, and manage cloud database transactions."
            },
        ],
    },
    "Digital Marketing": {
        "skills": [
            "SEO", "Content Writing", "Google Analytics", "Social Media Marketing",
            "Email Marketing", "SEM", "Canva", "Copywriting"
        ],
        "description": (
            "Plan and execute digital marketing campaigns, optimize content "
            "for search engines, and analyze campaign performance using "
            "analytics tools."
        ),
        "internships": [
            {
                "id": "aicte-dm-digitalindia",
                "title": "Digital Outreach & Social Media Intern",
                "company": "Digital India Corporation & AICTE",
                "portal_type": "AICTE Official Partner",
                "portal_url": "https://internship.aicte-india.org/",
                "location": "New Delhi / Remote",
                "stipend": "₹10,000 / month",
                "duration": "3 Months",
                "openings": "75 Openings",
                "skills_required": ["Social Media Marketing", "Content Writing", "Canva", "Copywriting"],
                "description": "Craft public awareness campaigns, coordinate digital outreach for citizen initiatives, and design engaging infographics."
            },
            {
                "id": "pmis-dm-tataconsumer",
                "title": "Brand & Performance Marketing Intern",
                "company": "Tata Consumer Products (PMIS)",
                "portal_type": "PM Internship Scheme (PMIS)",
                "portal_url": "https://pminternship.mca.gov.in/",
                "location": "Mumbai / Remote",
                "stipend": "₹5,000 (Govt) + ₹6,000 Allowance",
                "duration": "3 Months",
                "openings": "50 Openings",
                "skills_required": ["Google Analytics", "SEO", "SEM", "Email Marketing"],
                "description": "Analyze digital funnel conversion, optimize search engine rankings, and evaluate ad campaign return on ad spend (ROAS)."
            },
            {
                "id": "tulip-dm-tourism",
                "title": "Smart City Communications & Tourism Intern",
                "company": "Smart Cities Mission (MoHUA - TULIP)",
                "portal_type": "TULIP (MoHUA)",
                "portal_url": "https://internship.aicte-india.org/",
                "location": "Jaipur / Lucknow",
                "stipend": "₹8,000 / month",
                "duration": "4 Months",
                "openings": "20 Openings",
                "skills_required": ["Content Writing", "Canva", "Social Media Marketing"],
                "description": "Showcase urban heritage rejuvenation projects and drive public engagement for smart city tourism portals."
            },
        ],
    },
}

# Mock interview question bank per domain (used as seed and fallback)
INTERVIEW_QUESTIONS = {
    "Web Development": [
        "Explain the difference between HTML, CSS and JavaScript, and how they work together.",
        "How would you make a web page responsive across screen sizes?",
        "Describe how a REST API call flows from the frontend to the backend and back.",
    ],
    "AI / Machine Learning": [
        "What is the difference between supervised and unsupervised learning?",
        "How does gradient descent optimize a model's parameters?",
        "Explain what embeddings are and why they are useful in NLP.",
    ],
    "Data Science": [
        "How do you handle missing values in a dataset?",
        "Explain the difference between correlation and causation with an example.",
        "When would you choose SQL over Pandas for data analysis?",
    ],
    "Software Engineering": [
        "Explain the concept of OOP and its four main pillars.",
        "What is time complexity, and why does Big O notation matter?",
        "How does a hash map work internally?",
    ],
    "Digital Marketing": [
        "What is the difference between on-page and off-page SEO?",
        "How do you measure the success of a social media marketing campaign?",
        "Explain what a conversion funnel is and how you would optimize it.",
    ],
}
