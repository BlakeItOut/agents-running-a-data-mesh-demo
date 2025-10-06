/**
 * Solution/Clarity section slides (~5 minutes)
 */

function addSolutionSlides(presentationId) {
  Logger.log('Adding solution slides...');

  // Slide 8: A New Mental Model
  addContentSlide(
    presentationId,
    'A New Mental Model',
    '"What if every developer had a senior data architect as a pair-programmer?"\n\n' +
    'The AI Agent Team:\n' +
    '• Knows the best practices and platform standards\n' +
    '• Handles the boilerplate and configuration\n' +
    '• Enforces governance by default\n' +
    '• Lets developers focus on business logic\n\n' +
    'Not replacement. Augmentation.'
  );

  // Slide 9: Meet the Agent Team
  const agentList = CONFIG.AGENTS.map(agent =>
    agent.emoji + ' ' + agent.name + ': ' + agent.description
  );

  addBulletSlide(
    presentationId,
    'Meet the Agent Team',
    agentList
  );

  // Slide 10: The "Contribution First" Workflow
  addBulletSlide(
    presentationId,
    'The "Contribution First" Workflow',
    [
      'Agents don\'t deploy directly to production',
      'Instead, they generate a perfect starting point: a Pull Request',
      'Humans review, validate, and approve',
      'Governance is built-in, not bolted on',
      'Knowledge transfer happens through readable code and documentation'
    ]
  );

  Logger.log('✓ Solution slides complete');
}
