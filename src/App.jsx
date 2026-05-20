import {
  ArrowUp,
  ArrowUpRight,
  BookOpen,
  Download,
  Github,
  Linkedin,
  Mail,
  MapPin,
  ServerCog,
  Terminal
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
    const sections = document.querySelectorAll(".reveal-section");
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-visible");
          }
        });
      },
      { threshold: 0.18 }
    );

    sections.forEach((section) => observer.observe(section));

    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    const ids = ["about", "experience", "projects", "skills", "blog", "achievements", "contact"];
    const sections = ids
      .map((id) => document.getElementById(id))
      .filter(Boolean);

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setActiveSection(entry.target.id);
          }
        });
      },
      {
        rootMargin: "-35% 0px -55%",
        threshold: 0.01
      }
    );

    sections.forEach((section) => observer.observe(section));

    return () => observer.disconnect();
  }, []);

  return (
    <main className="page-shell">
      <div className="scroll-progress" style={{ width: `${scrollProgress}%` }} />
      <nav className="nav">
        <a href="#top" className="brand">
          DM
        </a>
        <div className="nav-links">
          <a href="#about" className={activeSection === "about" ? "is-active" : ""}>About</a>
          <a href="#experience" className={activeSection === "experience" ? "is-active" : ""}>Experience</a>
          <a href="#projects" className={activeSection === "projects" ? "is-active" : ""}>Projects</a>
          <a href="#skills" className={activeSection === "skills" ? "is-active" : ""}>Skills</a>
          <a href="#blog" className={`nav-blog ${activeSection === "blog" ? "is-active" : ""}`} aria-label="View blog section">
            <BookOpen size={16} />
            Blog
          </a>
          <a href="#contact" className={activeSection === "contact" ? "is-active" : ""}>Contact</a>
        </div>
      </nav>

      <section id="top" className="hero">
        <div className="hero-copy">
          <p className="eyebrow">DevOps • Cloud Infrastructure • Platform Engineering</p>
          <h1>{profile.name}</h1>
          <p className="hero-role">{profile.role}</p>
          <p className="hero-tagline">{profile.tagline}</p>
          <div className="hero-stats" aria-label="Career highlights">
            <span>
              <strong>4+</strong>
              Years
            </span>
            <span>
              <strong>40%</strong>
              Faster deploys
            </span>
            <span>
              <strong>60%</strong>
              Fewer errors
            </span>
          </div>
          <div className="hero-actions">
            <a href="#projects" className="button button-primary">
              <ServerCog size={18} />
              View Projects
            </a>
            <a href={profile.resumeUrl} className="button button-secondary" download>
              <Download size={18} />
              Resume
            </a>
            <a href="/blog" className="button button-secondary">
              <BookOpen size={18} />
              Blog
            </a>
          </div>
          <div className="devops-command" aria-label="DevOps workflow summary">
            <Terminal size={17} />
            <code>$ deploy --reliable --observable</code>
          </div>
          <div className="hero-meta">
            <span>
              <MapPin size={16} />
              {profile.location}
            </span>
            <a href={socialLinks.linkedin} target="_blank" rel="noreferrer">
              <Linkedin size={16} />
              LinkedIn
            </a>
          </div>
        </div>
        <div className="hero-visual">
          <img src={profile.photo} alt="Portrait of Divyam Matia" />
        </div>
      </section>

      <Section id="about" eyebrow="About" title="Building infrastructure that stays calm under pressure.">
        <p className="lede">{profile.summary}</p>
        <div className="ops-strip" aria-label="DevOps operating model">
          <span><Terminal size={16} /> Code</span>
          <span>Validate</span>
          <span><ServerCog size={16} /> Provision</span>
          <span>Deploy</span>
          <span>Observe</span>
        </div>
      </Section>

      <Section id="experience" eyebrow="Experience" title="A career built around dependable delivery.">
        <div className="timeline">
          {experience.map((item) => (
            <article className="timeline-item" key={`${item.company}-${item.role}`}>
              <div className="timeline-heading">
                <h3>{item.role}</h3>
                <span>{item.period}</span>
              </div>
              <p className="company">{item.company}</p>
              <ul>
                {item.highlights.map((highlight) => (
                  <li key={highlight}>{highlight}</li>
                ))}
              </ul>
            </article>
          ))}
        </div>
      </Section>

      <Section id="projects" eyebrow="Projects" title="Selected work across automation and platform engineering.">
        <div className="card-grid">
          {projects.map((project, index) => (
            <article className="project-card" key={project.title}>
              <div className="project-index">0{index + 1}</div>
              <div className="project-heading">
                <h3>{project.title}</h3>
                {project.link !== "#" && (
                  <a href={project.link} aria-label={`Open ${project.title}`}>
                    <ArrowUpRight size={18} />
                  </a>
                )}
              </div>
              <p className="project-problem">{project.problem}</p>
              <p>{project.details}</p>
              <div className="tag-row">
                {project.stack.map((item) => (
                  <span key={item}>{item}</span>
                ))}
              </div>
            </article>
          ))}
        </div>
      </Section>

      <Section id="skills" eyebrow="Skills" title="Tools are useful. Systems thinking is the multiplier.">
        <div className="skills-grid">
          {skills.map((skill) => (
            <article className="skill-card" key={skill.group}>
              <h3>{skill.group}</h3>
              <div className="tag-row">
                {skill.items.map((item) => (
                  <span key={item}>{item}</span>
                ))}
              </div>
            </article>
          ))}
        </div>
      </Section>

      <Section id="blog" eyebrow="Writing" title="DevOps notes from real delivery work.">
        <div className="blog-grid">
          {blogPosts.map((post, index) => (
            <a className="blog-card" href={`/blog/${post.slug}/`} key={post.slug}>
              <span className="blog-number">0{index + 1}</span>
              <div>
                <p className="blog-meta">{post.date} | {post.readTime}</p>
                <h3>{post.title}</h3>
                <p>{post.summary}</p>
              </div>
              <div className="tag-row">
                {post.tags.map((tag) => (
                  <span key={tag}>{tag}</span>
                ))}
              </div>
            </a>
          ))}
        </div>
        <a href="/blog" className="blog-index-link">
          <BookOpen size={18} />
          Open full blog
        </a>
      </Section>

      <Section id="achievements" eyebrow="Milestones" title="Achievements">
        <div className="achievement-grid">
          {achievements.map((item, index) => (
            <article className="achievement-card" key={item}>
              <span>0{index + 1}</span>
              <p>{item}</p>
            </article>
          ))}
        </div>
      </Section>

      <Section id="contact" eyebrow="Contact" title="Let’s build systems people can rely on.">
        <div className="contact-card">
          <p>
            Open to conversations around DevOps engineering, cloud delivery, and platform reliability.
          </p>
          <div className="contact-links">
            <a href={socialLinks.email} className="contact-primary">
              <Mail size={18} />
              Email
            </a>
            <a href={socialLinks.linkedin} target="_blank" rel="noreferrer">
              <Linkedin size={18} />
              LinkedIn
            </a>
            <a href={socialLinks.github} target="_blank" rel="noreferrer">
              <Github size={18} />
              GitHub
            </a>
          </div>
        </div>
      </Section>

      <a
        href="#top"
        className={`back-to-top ${showBackToTop ? "is-visible" : ""}`}
        aria-label="Back to top"
      >
        <ArrowUp size={20} />
      </a>
    </main>
  );
}

export default App;
