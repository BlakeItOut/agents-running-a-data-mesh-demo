/**
 * Conclusion section slides (~5 minutes)
 */

function addConclusionSlides(presentationId) {
  Logger.log('Adding conclusion slides...');

  // Slide: The Agentic Lifecycle Revisited
  addContentSlide(
    presentationId,
    'The Agentic Lifecycle Revisited',
    'What we just saw:\n\n' +
    '🏗️ Design → ⚙️ Scaffold → 💻 Implement → 📚 Document → 🔍 Operate\n\n' +
    'Each agent is a specialist in its domain.\n' +
    'Together, they form a complete development team.\n' +
    'Humans remain in control, reviewing and approving each step.'
  );

  // Slide: Key Takeaways
  addBulletSlide(
    presentationId,
    'Key Takeaways',
    [
      'Specialization over Generalization: A team of focused agents is more powerful than one generalist',
      'Humans in the Loop: Augmentation, not replacement. Developers review and approve all changes.',
      'From Months to Minutes: Transform the economics of data product development',
      'Built-in Governance: Standards and best practices are enforced by default, not bolted on afterward',
      'Knowledge Transfer: Every PR is a learning opportunity through readable code and documentation'
    ]
  );

  // Slide: What's Next?
  addBulletSlide(
    presentationId,
    'What\'s Next?',
    [
      'Proactive Agents: Suggest schema migrations before breaking changes occur',
      'Quality Automation: Detect data quality issues and auto-generate remediation PRs',
      'Performance Optimization: Autonomous tuning of data flows based on usage patterns',
      'Cross-Domain Discovery: Recommend related data products and reusable components',
      'Self-Healing Systems: Agents that detect and fix common operational issues'
    ]
  );

  // Slide: The Bigger Picture
  addContentSlide(
    presentationId,
    'The Bigger Picture',
    'This isn\'t just about data products.\n\n' +
    'It\'s about fundamentally rethinking how we build platforms:\n\n' +
    '• Reduce cognitive load on developers\n' +
    '• Encode institutional knowledge in agents\n' +
    '• Make the "right way" the easy way\n' +
    '• Enable teams to move fast without breaking things\n\n' +
    'AI agents can finally deliver on the promise of the Data Mesh.'
  );

  // Final Slide: Thank You
  addTitleSlide(
    presentationId,
    'Thank You!',
    'Questions?\n\n' +
    CONFIG.AUTHOR.email + '\n' +
    CONFIG.AUTHOR.blog
  );

  Logger.log('✓ Conclusion slides complete');
}
