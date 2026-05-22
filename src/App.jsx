import {
  ArrowUp,
  ArrowUpRight,
  BriefcaseBusiness,
  BookOpen,
  CircleUserRound,
  Command,
  Download,
  FileText,
  GitBranch,
  Github,
  Layers3,
  Linkedin,
  Mail,
  MapPin,
  Moon,
  Network,
  ServerCog,
  ShieldCheck,
  Sun,
  Terminal,
  Workflow
} from "lucide-react";
import { useEffect, useState } from "react";
import {
  achievements,
  blogPosts,
  experience,
  profile,
  projects,
  skills,
  socialLinks
} from "./content.js";

const stackGroups = [
  { label: "Plan", icon: GitBranch, tools: ["Jira", "Azure Boards", "ServiceNow"] },
  { label: "Build", icon: Workflow, tools: ["Azure DevOps", "GitHub Actions", "GitLab", "Jenkins"] },
  { label: "Provision", icon: Layers3, tools: ["Terraform", "Ansible", "ARM Templates"] },
  { label: "Deploy", icon: ServerCog, tools: ["Kubernetes", "Docker", "Helm", "Argo CD", "Flux CD"] },
  { label: "Secure", icon: ShieldCheck, tools: ["SonarQube", "Snyk", "Trivy", "Checkov", "OWASP ZAP"] },
  { label: "Observe", icon: Network, tools: ["Azure Monitor", "App Insights", "Elasticsearch", "Prometheus"] }
];

const resumeHighlights = [
  "4+ years across DevOps, cloud infrastructure, CI/CD, and Kubernetes delivery.",
  "40% faster release deployments with 60% fewer manual errors in production-facing workflows.",
  "50% faster Azure DevOps environment setup through Ansible-based platform automation."
];

const architectureFlows = [
  { title: "CI/CD Release Flow", stages: ["Commit", "Build", "Scan", "Deploy", "Observe"] },
  { title: "IaC Delivery Flow", stages: ["Plan", "Validate", "Cost", "Approve", "Apply"] },
  { title: "DevSecOps Gate", stages: ["Code", "SAST", "SCA", "Container", "DAST"] }
];

const constellation = ["Terraform", "AKS", "Azure DevOps", "Ansible", "Trivy", "GitLab", "Helm", "Monitor"];

function Section({ id, eyebrow, title, children }) {
  return (
    <section id={id} className="section reveal-section">
      <div className="section-heading">
        <p className="eyebrow">{eyebrow}</p>
        <h2>{title}</h2>
      </div>
      {children}
    </section>
  );
}

function App() {
  const [scrollProgress, setScrollProgress] = useState(0);
  const [showBackToTop, setShowBackToTop] = useState(false);
  const [activeSection, setActiveSection] = useState("about");
  const [commandOpen, setCommandOpen] = useState(false);
  const [theme, setTheme] = useState(() => {
    if (typeof window === "undefined") return "dark";
    return localStorage.getItem("theme") || "dark";
  });

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    localStorage.setItem("theme", theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme((currentTheme) => (currentTheme === "dark" ? "light" : "dark"));
  };

  useEffect(() => {
    const handleScroll = () => {
      const scrollableHeight =
        document.documentElement.scrollHeight - window.innerHeight;
      const progress =
        scrollableHeight > 0 ? (window.scrollY / scrollableHeight) * 100 : 0;

      setScrollProgress(progress);
      setShowBackToTop(window.scrollY > 420);
    };

    handleScroll();
    window.addEventListener("scroll", handleScroll, { passive: true });

    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  useEffect(() => {
    const handleKeyDown = (event) => {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        setCommandOpen((open) => !open);
      }
      if (event.key === "Escape") setCommandOpen(false);
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  useEffect(() => {
    const sections = document.querySelectorAll(".reveal-section");
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) entry.target.classList.add("is-visible");
        });
      },
      { threshold: 0.18 }
    );

    sections.forEach((section) => observer.observe(section));
    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    const ids = ["about", "experience", "projects", "architecture", "skills", "stack", "blog", "achievements", "contact"];
    const sections = ids.map((id) => document.getElementById(id)).filter(Boolean);
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) setActiveSection(entry.target.id);
        });
      },
      { rootMargin: "-35% 0px -55%", threshold: 0.01 }
    );

    sections.forEach((section) => observer.observe(section));
    return () => observer.disconnect();
  }, []);

  const commandItems = [
    { label: "Open resume", href: profile.resumeUrl, icon: FileText },
    { label: "View projects", href: "#projects", icon: ServerCog },
    { label: "Read blog", href: "/blog", icon: BookOpen },
    { label: "Email Divyam", href: socialLinks.email, icon: Mail },
    { label: "Open GitHub", href: socialLinks.github, icon: Github }
  ];

  return (
    <main className="page-shell">
      <div className="scroll-progress" style={{ width: `${scrollProgress}%` }} />
      <div className="tool-constellation" aria-hidden="true">
        {constellation.map((tool, index) => (
          <span key={tool} className={`tool-float tool-${index + 1}`}>{tool}</span>
        ))}
      </div>

      <nav className="nav">
        <a href="#top" className="brand">DM</a>
        <div className="nav-links">
          <a href="#about" className={activeSection === "about" ? "is-active" : ""}><CircleUserRound size={16} />About</a>
          <a href="#experience" className={activeSection === "experience" ? "is-active" : ""}><BriefcaseBusiness size={16} />Experience</a>
          <a href="#projects" className={activeSection === "projects" ? "is-active" : ""}><ServerCog size={16} />Projects</a>
          <a href="#stack" className={activeSection === "stack" || activeSection === "skills" ? "is-active" : ""}><Layers3 size={16} />Stack</a>
          <a href="#blog" className={activeSection === "blog" ? "is-active" : ""} aria-label="View blog section"><BookOpen size={16} />Blog</a>
          <a href="#contact" className={activeSection === "contact" ? "is-active" : ""}><Mail size={16} />Contact</a>
        </div>
        <button className="theme-toggle" type="button" onClick={toggleTheme} aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}>
          {theme === "dark" ? <Sun size={18} /> : <Moon size={18} />}
          <span>{theme === "dark" ? "Light" : "Dark"}</span>
        </button>
      </nav>

      <section id="top" className="hero">
        <div className="hero-copy">
          <div className="pipeline-beam" aria-hidden="true"><span></span><span></span><span></span><span></span></div>
          <p className="eyebrow">DevOps | Cloud Infrastructure | Platform Engineering</p>
          <h1>{profile.name}</h1>
          <p className="hero-role">{profile.role}</p>
          <p className="hero-tagline">{profile.tagline}</p>
          <div className="hero-stats" aria-label="Career highlights">
            <span><strong>4+</strong>Years</span>
            <span><strong>40%</strong>Faster deploys</span>
            <span><strong>60%</strong>Fewer errors</span>
          </div>
          <div className="hero-actions">
            <a href="#projects" className="button button-primary"><ServerCog size={18} />View Projects</a>
            <a href={profile.resumeUrl} className="button button-secondary" download><Download size={18} />Resume</a>
            <a href="/blog" className="button button-secondary"><BookOpen size={18} />Blog</a>
          </div>
          <div className="devops-command" aria-label="DevOps workflow summary"><Terminal size={17} /><code>$ deploy --reliable --observable</code></div>
          <div className="hero-meta">
            <span><MapPin size={16} />{profile.location}</span>
            <a href={socialLinks.linkedin} target="_blank" rel="noreferrer"><Linkedin size={16} />LinkedIn</a>
          </div>
        </div>
        <div className="hero-visual photo-frame">
          <img src={profile.photo} alt="Portrait of Divyam Matia" />
        </div>
      </section>

      <Section id="about" eyebrow="About" title="Building infrastructure that stays calm under pressure.">
        <p className="lede">{profile.summary}</p>
        <div className="ops-strip" aria-label="DevOps operating model">
          <span><Terminal size={16} /> Code</span><span>Validate</span><span><ServerCog size={16} /> Provision</span><span>Deploy</span><span>Observe</span>
        </div>
      </Section>

      <Section id="resume" eyebrow="Resume" title="The strongest signals before the PDF opens.">
        <div className="resume-grid">
          {resumeHighlights.map((item, index) => (
            <article className="resume-card" key={item}><span>signal 0{index + 1}</span><p>{item}</p></article>
          ))}
        </div>
      </Section>

      <Section id="experience" eyebrow="Experience" title="A career built around dependable delivery.">
        <div className="timeline">
          {experience.map((item) => (
            <article className="timeline-item" key={`${item.company}-${item.role}`}>
              <div className="timeline-heading"><h3>{item.role}</h3><span>{item.period}</span></div>
              <p className="company">{item.company}</p>
              <ul>{item.highlights.map((highlight) => <li key={highlight}>{highlight}</li>)}</ul>
            </article>
          ))}
        </div>
      </Section>

      <Section id="projects" eyebrow="Projects" title="Selected work across automation and platform engineering.">
        <div className="card-grid">
          {projects.map((project, index) => (
            <a className="project-card" href={project.link} key={project.title}>
              <div className="project-index">0{index + 1}</div>
              <div className="project-heading"><h3>{project.title}</h3><ArrowUpRight size={18} /></div>
              <p className="project-status">queued -&gt; validating -&gt; deployed</p>
              <p className="project-problem">{project.problem}</p>
              <p>{project.details}</p>
              <div className="tag-row">{project.stack.map((item) => <span key={item}>{item}</span>)}</div>
            </a>
          ))}
        </div>
      </Section>

      <Section id="architecture" eyebrow="Architecture" title="Delivery flows made visible.">
        <div className="architecture-grid">
          {architectureFlows.map((flow) => (
            <article className="architecture-card" key={flow.title}>
              <h3>{flow.title}</h3>
              <div className="flow-line">{flow.stages.map((stage) => <span key={stage}>{stage}</span>)}</div>
            </article>
          ))}
        </div>
      </Section>

      <Section id="skills" eyebrow="Skills" title="Tools are useful. Systems thinking is the multiplier.">
        <div className="skills-grid">
          {skills.map((skill) => (
            <article className="skill-card" key={skill.group}>
              <h3>{skill.group}</h3>
              <div className="tag-row">{skill.items.map((item) => <span key={item}>{item}</span>)}</div>
            </article>
          ))}
        </div>
      </Section>

      <Section id="stack" eyebrow="Stack Map" title="A DevOps stack organized by delivery stage.">
        <div className="stack-map">
          {stackGroups.map(({ label, icon: Icon, tools }) => (
            <article className="stack-node" key={label}>
              <div className="stack-node-heading"><Icon size={18} /><h3>{label}</h3></div>
              <div className="tag-row">{tools.map((tool) => <span key={tool}>{tool}</span>)}</div>
            </article>
          ))}
        </div>
      </Section>

      <Section id="blog" eyebrow="Writing" title="DevOps notes from real delivery work.">
        <div className="blog-grid">
          {blogPosts.map((post, index) => (
            <a className="blog-card" href={`/blog/${post.slug}/`} key={post.slug}>
              <span className="blog-number">0{index + 1}</span>
              <div><p className="blog-meta">{post.date} | {post.readTime}</p><h3>{post.title}</h3><p>{post.summary}</p></div>
              <div className="tag-row">{post.tags.map((tag) => <span key={tag}>{tag}</span>)}</div>
            </a>
          ))}
        </div>
        <a href="/blog" className="blog-index-link"><BookOpen size={18} />Open full blog</a>
      </Section>

      <Section id="achievements" eyebrow="Milestones" title="Achievements">
        <div className="achievement-grid">
          {achievements.map((item, index) => <article className="achievement-card" key={item}><span>0{index + 1}</span><p>{item}</p></article>)}
        </div>
      </Section>

      <Section id="contact" eyebrow="Contact" title="Let's build systems people can rely on.">
        <div className="contact-card">
          <p>Open to conversations around DevOps engineering, cloud delivery, and platform reliability.</p>
          <div className="contact-links">
            <a href={socialLinks.email} className="contact-primary"><Mail size={18} />Email</a>
            <a href={socialLinks.linkedin} target="_blank" rel="noreferrer"><Linkedin size={18} />LinkedIn</a>
            <a href={socialLinks.github} target="_blank" rel="noreferrer"><Github size={18} />GitHub</a>
          </div>
        </div>
      </Section>

      <button className="command-button" type="button" onClick={() => setCommandOpen(true)} aria-label="Open command palette"><Command size={20} /></button>

      {commandOpen && (
        <div className="command-overlay" role="dialog" aria-modal="true" aria-label="Command palette">
          <button className="command-backdrop" type="button" onClick={() => setCommandOpen(false)} aria-label="Close command palette" />
          <div className="command-panel">
            <div className="command-panel-header"><Command size={18} /><span>Run action</span><kbd>Esc</kbd></div>
            {commandItems.map(({ label, href, icon: Icon }) => (
              <a className="command-item" href={href} key={label} onClick={() => setCommandOpen(false)}><Icon size={18} /><span>{label}</span><small>execute</small></a>
            ))}
          </div>
        </div>
      )}

      <a href="#top" className={`back-to-top ${showBackToTop ? "is-visible" : ""}`} aria-label="Back to top"><ArrowUp size={20} /></a>
    </main>
  );
}

export default App;
