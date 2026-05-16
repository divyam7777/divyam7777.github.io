export const profile = {
  name: "Divyam Matia",
  role: "DevOps Engineer",
  tagline:
    "Designing faster, safer delivery systems across cloud infrastructure, Kubernetes, and CI/CD.",
  location: "New Delhi, India",
  summary:
    "DevOps and infrastructure engineer with 4+ years of experience designing deployment pipelines, automating cloud infrastructure, and improving delivery reliability across Azure and AWS. My work spans Azure DevOps, GitHub Actions, GitLab, Terraform, Ansible, Kubernetes, Docker, and DevSecOps tooling, with a bias toward infrastructure that is repeatable, observable, and easier for teams to trust.",
  photo: "/profile-placeholder.jpg",
  resumeUrl: "/Divyam_Matia_Resume.pdf"
};

export const socialLinks = {
  email: "mailto:divyammatia77@gmail.com",
  linkedin: "https://www.linkedin.com/in/divyam-matia",
  github: "https://github.com/divyam7777"
};

export const experience = [
  {
    company: "Saxo Bank",
    role: "DevOps Engineer",
    period: "Oct 2024 — Present",
    highlights: [
      "Engineered Azure DevOps release pipelines for Windows and Kubernetes services, enabling weekly Live Service Upgrades with 40% faster deployment times and 60% fewer manual errors.",
      "Designed end-to-end DevOps workflows across pipeline creation, Kubernetes deployment, and security-tool integration with cross-functional teams.",
      "Troubleshoot environment issues, isolate failing services, and support client test environments for Saxo Bank trading platforms."
    ]
  },
  {
    company: "Unisys",
    role: "DevOps Engineer",
    period: "Jul 2022 — Sep 2024",
    highlights: [
      "Built an Ansible playbook that automated Azure DevOps setup end to end, including service connections, extensions, pipelines, releases, and project creation, reducing deployment time by 50%.",
      "Created Azure DevOps data pipelines for Azure Data Factory and Azure Databricks in restricted-network environments.",
      "Engineered Terraform-based IaC pipelines through Azure DevOps and GitLab, delivering 40% faster infrastructure deployments and 60% fewer manual errors.",
      "Integrated a broad DevSecOps toolchain including SonarQube, Snyk, Trivy, Checkov, Grype, OWASP ZAP, Selenium, Terratest, and Infracost."
    ]
  },
  {
    company: "Unisys",
    role: "Technical Intern",
    period: "Oct 2021 — Jun 2022",
    highlights: [
      "Designed CI/CD pipelines with Azure DevOps and Jenkins for Python, Java, and JavaScript workloads.",
      "Used AKS for deployments and integrated Prometheus and Grafana for monitoring.",
      "Implemented Infrastructure as Code with Terraform and Ansible to improve scalability and reliability."
    ]
  }
];

export const projects = [
  {
    title: "Release Automation for Windows and Kubernetes Services",
    problem:
      "Weekly service upgrades were vulnerable to slow manual release work and avoidable deployment mistakes.",
    details:
      "Built Azure DevOps release pipelines for Windows services and Kubernetes services, improving deployment speed by 40% while cutting manual errors by 60%.",
    stack: ["Azure DevOps", "Kubernetes", "Release Engineering"],
    link: "#"
  },
  {
    title: "Azure DevOps Environment Provisioning Automation",
    problem:
      "Creating projects, service connections, extensions, and pipelines by hand made setup slow and inconsistent.",
    details:
      "Developed an Ansible playbook that automated Azure DevOps project creation, pipeline setup, release configuration, and execution, reducing deployment time by 50%.",
    stack: ["Ansible", "Azure DevOps", "Automation"],
    link: "#"
  },
  {
    title: "IaC Delivery Pipelines for Azure Infrastructure",
    problem:
      "Infrastructure changes needed a faster, safer path from code to production.",
    details:
      "Engineered Terraform Cloud pipelines with Azure DevOps and GitLab for Azure infrastructure, delivering 40% faster deployments and 60% fewer manual errors.",
    stack: ["Terraform", "GitLab", "Azure", "IaC"],
    link: "#"
  },
  {
    title: "Restricted-Network Data Platform Pipelines",
    problem:
      "Azure Data Factory and Azure Databricks resources needed deployment automation without external network access.",
    details:
      "Created Azure DevOps data pipelines that supported private-resource deployment workflows for locked-down environments.",
    stack: ["Azure Data Factory", "Azure Databricks", "Azure DevOps"],
    link: "#"
  },
  {
    title: "Integrated DevSecOps Quality Pipeline",
    problem:
      "Security, compliance, and testing often become scattered checks instead of a coherent release gate.",
    details:
      "Implemented a streamlined pipeline integrating code quality, SCA, container scanning, IaC validation, dynamic testing, infra cost checks, and automated tests.",
    stack: ["SonarQube", "Snyk", "Trivy", "Checkov", "OWASP ZAP", "Selenium"],
    link: "#"
  }
];

export const skills = [
  {
    group: "Cloud & Platform",
    items: ["Azure", "AWS", "Azure API Management", "Azure Key Vault", "Azure App Services"]
  },
  {
    group: "Infrastructure & Containers",
    items: ["Terraform", "Ansible", "ARM Templates", "Kubernetes", "Docker", "Helm", "K9s"]
  },
  {
    group: "CI/CD & GitOps",
    items: ["Azure DevOps", "GitLab", "GitHub Actions", "Argo CD", "Flux CD", "Jenkins"]
  },
  {
    group: "Monitoring & Delivery",
    items: ["Azure Monitor", "Application Insights", "Elasticsearch", "Nginx", "Jira", "ServiceNow"]
  },
  {
    group: "Languages & Frameworks",
    items: ["Python", "Bash", "SQL", "Jinja", "FastAPI", "Django", "YAML", "JSON"]
  },
  {
    group: "Security & Testing",
    items: ["SonarQube", "Snyk", "Trivy", "Checkov", "Terratest", "OWASP ZAP", "Selenium"]
  }
];

export const achievements = [
  "9.3 CGPA at Chitkara University",
  "40% faster release deployments with 60% fewer manual errors at Saxo Bank",
  "50% reduction in Azure DevOps environment setup time through Ansible automation",
  "40% faster infrastructure deployments with 60% fewer manual errors using Terraform-based IaC pipelines"
];
