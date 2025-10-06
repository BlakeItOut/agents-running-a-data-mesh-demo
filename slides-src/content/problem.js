/**
 * Problem/Chaos section slides (~10 minutes)
 */

function addProblemSlides(presentationId) {
  Logger.log('Adding problem slides...');

  // Slide 4: The Reality of Data Platforms
  addBulletSlide(
    presentationId,
    'The Reality of Data Platforms',
    [
      'The dream: Self-service data access for all teams',
      'The reality: Overwhelming cognitive overload',
      'Every team needs expertise in Kafka, Kubernetes, Terraform, schemas, governance...',
      'The "self-serve" platform is often just a pile of complex tools with poor documentation'
    ]
  );

  // Slide 5: The Data Mesh Promise vs Reality
  addTwoColumnSlide(
    presentationId,
    'The "Data Mesh" Promise vs. The Reality',
    'PROMISE:\n• Domain Ownership\n• Data as a Product\n• Self-Serve Platform\n• Federated Governance',
    'REALITY:\n• Requires immense discipline\n• Huge platform team needed\n• Extensive developer training\n• High initial friction kills adoption'
  );

  // Slide 6: The Data Product Lifecycle is Broken
  addSectionHeaderSlide(
    presentationId,
    'The Data Product Lifecycle is Broken'
  );

  addBulletSlide(
    presentationId,
    'Friction at Every Stage',
    [
      '📐 Design: Endless meetings, inconsistent schemas, no clear standards',
      '🏗️ Scaffold: Copy-paste errors, forgotten governance steps, configuration drift',
      '💻 Implement: Repetitive boilerplate code, testing overhead, slow iteration',
      '📚 Document: Always an afterthought, quickly becomes stale and inaccurate',
      '🔍 Operate: What should we monitor? How do we build dashboards? Who gets alerted?'
    ]
  );

  // Slide 7: The Core Problem
  addContentSlide(
    presentationId,
    'The Core Problem: The "First Mile"',
    'Getting started is the hardest part.\n\n' +
    'The initial friction of creating a new, well-governed, and properly structured data product is too high.\n\n' +
    'This leads to:\n' +
    '• Shortcuts and workarounds\n' +
    '• Inconsistent implementations\n' +
    '• Technical debt from day one\n' +
    '• Ultimately, a failed data mesh initiative'
  );

  Logger.log('✓ Problem slides complete');
}
