import {
  ArrowUp,
  ArrowUpRight,
  Download,
  Github,
  Linkedin,
  Mail,
  MapPin
} from "lucide-react";
import { useEffect, useState } from "react";
import {
  achievements,
  experience,
  profile,
  projects,
  skills,
  socialLinks
} from "./content.js";

function Section({ id, eyebrow, title, children }) {
  return (
    <section id={id} className="section">
      <p className="eyebrow">{eyebrow}</p>
      <h2>{title}</h2>
      {children}
    </section>
  );
}

function App() {
  const [scrollProgress, setScrollProgress] = useState(0);
  const [showBackToTop, setShowBackToTop] = useState(false);

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

  return (
    <main className="page-shell">
      <div className="scroll-progress" style={{ width: `${scrollProgress}%` }} />
      <nav className="nav">
        <a href="#top" className="brand">
          DM
        </a>
        <div className="nav-links">
          <a href="#about">About</a>
          <a href="#experience">Experience</a>
          <a href="#projects">Projects</a>
          <a href="#contact">Contact</a>
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
              <strong>3+</strong>
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
              View Projects
            </a>
            <a href={profile.resumeUrl} className="button button-secondary" download>
              <Download size={18} />
              Resume
            </a>
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
          {projects.map((project) => (
            <article className="project-card" key={project.title}>
              <div className="project-heading">
                <h3>{project.title}</h3>
                <a href={project.link} aria-label={`Open ${project.title}`}>
                  <ArrowUpRight size={18} />
                </a>
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

      <Section id="achievements" eyebrow="Milestones" title="Achievements">
        <ul className="clean-list">
          {achievements.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </Section>

      <Section id="contact" eyebrow="Contact" title="Let’s build systems people can rely on.">
        <div className="contact-card">
          <p>
            Open to conversations around DevOps engineering, cloud delivery, and platform reliability.
          </p>
          <div className="contact-links">
            <a href={socialLinks.email}>
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
