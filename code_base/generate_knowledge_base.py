import os

# 🔹 Knowledge base directory
BASE_DIR = "/mnt/f/projects/ai-recall-system/agent_knowledge_bases"

# 🔹 Predefined knowledge content for each agent
KNOWLEDGE_CONTENT = {
    "architect_knowledge": """# AI System Architecture Principles

## 1. Modular Design
- Split the system into independent modules that communicate via APIs.
- Each module should have a clear **responsibility** (e.g., data handling, ML models, UI).

## 2. Scalability
- Implement **horizontal scaling** where possible.
- Use **containerization (Docker/Kubernetes)** for deployment.

## 3. Versioning & Documentation
- Maintain a versioning system for architecture changes.
- Document all API interactions and agent workflows.

""",
    "engineer_knowledge": """# Software Engineering & API Best Practices

## 1. Clean Code
- Use **descriptive variable names** and **modular functions**.
- Follow **PEP8** for Python development.

## 2. API Development
- Use **Flask/FastAPI** for lightweight API services.
- Implement **rate limiting & authentication** for security.

## 3. Error Handling
- Use **try-except** blocks to prevent crashes.
- Log all **critical errors** for debugging.

""",
    "reviewer_knowledge": """# Code Review Best Practices

## 1. Code Readability
- Ensure consistent **code formatting** (Black, Flake8).
- Minimize **nested loops** and **complex logic**.

## 2. Security & Performance
- Validate **API inputs** against SQL injection and XSS attacks.
- Optimize **database queries** for speed.

""",
    "qa_knowledge": """# AI & Software Testing Strategies

## 1. Unit Testing
- Use **pytest** for automated unit tests.
- Test all **critical functions** before deployment.

## 2. Integration Testing
- Simulate real-world **user interactions**.
- Validate **API response consistency**.

## 3. Edge Case Handling
- Test for **invalid inputs**, **missing fields**, and **high loads**.

""",
    "devops_knowledge": """# DevOps & CI/CD Best Practices

## 1. Deployment Pipeline
- Use **GitHub Actions/Jenkins** for CI/CD.
- Automate **container builds** and **server deployments**.

## 2. Infrastructure as Code
- Use **Terraform** or **Ansible** to manage infrastructure.
- Avoid **manual server configuration**.

## 3. Monitoring & Logging
- Implement **Prometheus/Grafana** for real-time monitoring.
- Store logs using **ELK stack**.

""",
    "oversight_knowledge": """# AI Oversight & Compliance

## 1. Ethical AI Development
- Ensure **AI decisions are explainable** and **bias-free**.
- Comply with **GDPR** and **AI safety standards**.

## 2. Security Audits
- Regularly scan for **vulnerabilities in dependencies**.
- Use **role-based access control (RBAC)**.

## 3. System Integrity Checks
- Automate security scans for **code changes**.
- Require **human validation for major updates**.

""",
    "feedback_knowledge": """# AI Feedback & Continuous Learning

## 1. User Feedback Handling
- Log all **user complaints & feature requests**.
- Auto-categorize feedback by **priority & impact**.

## 2. AI Model Evaluation
- Monitor **LLM performance & hallucination rates**.
- Retrain AI models based on **real-world data**.

""",
}


def create_knowledge_bases():
    """Creates knowledge base directories & populates them with markdown content."""
    if not os.path.exists(BASE_DIR):
        os.makedirs(BASE_DIR)

    for folder, content in KNOWLEDGE_CONTENT.items():
        folder_path = os.path.join(BASE_DIR, folder)
        os.makedirs(folder_path, exist_ok=True)

        file_path = os.path.join(folder_path, "README.md")
        with open(file_path, "w") as f:
            f.write(content)

        print(f"✅ Generated {file_path}")


if __name__ == "__main__":
    create_knowledge_bases()
    print("🎉 All agent knowledge bases have been created and populated!")
