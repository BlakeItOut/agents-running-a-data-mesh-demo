/**
 * Configuration for the presentation theme and colors
 */

const CONFIG = {
  // Template presentation ID (contains the theme we want to use)
  THEME_PRESENTATION_ID: '10XqMMGWKuDichIWSMDeIw84KFgOSdZFS-5sv5avKYtk',

  // Presentation metadata
  PRESENTATION_TITLE: 'From Chaos to Clarity: Building a Data Mesh with an AI Agent Team',
  CONFERENCE: '[Your Conference Name]',

  // Author information (customize before presenting)
  AUTHOR: {
    name: '[Your Name]',
    title: '[Your Title]',
    company: '[Your Company]',
    email: '[Your Email]',
    blog: '[Your Blog/Website]'
  },

  // Theme colors (from the template)
  COLORS: {
    YELLOW: { red: 0.99, green: 0.82, blue: 0.15 },      // #FDB927
    CORAL: { red: 1.0, green: 0.43, blue: 0.38 },        // #FF6F61
    BLUE: { red: 0.26, green: 0.52, blue: 0.96 },        // #4285F4
    GREEN: { red: 0.06, green: 0.62, blue: 0.35 },       // #0F9D58
    LIGHT_GRAY: { red: 0.95, green: 0.95, blue: 0.95 }   // Background
  },

  // Agent team configuration
  AGENTS: [
    {
      name: 'The Architect',
      emoji: '🏗️',
      color: 'BLUE',
      description: 'Design and schema expert'
    },
    {
      name: 'The Engineer',
      emoji: '⚙️',
      color: 'YELLOW',
      description: 'Infrastructure and bootstrapping specialist'
    },
    {
      name: 'The Coder',
      emoji: '💻',
      color: 'CORAL',
      description: 'Pair-programmer for business logic and testing'
    },
    {
      name: 'The Scribe',
      emoji: '📚',
      color: 'GREEN',
      description: 'Documentation and cataloging assistant'
    },
    {
      name: 'The SRE',
      emoji: '🔍',
      color: 'CORAL',
      description: 'Site Reliability Expert for observability'
    }
  ]
};
