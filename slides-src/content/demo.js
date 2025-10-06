/**
 * Demo section slides (~25 minutes)
 */

function addDemoSlides(presentationId) {
  Logger.log('Adding demo slides...');

  // Demo Overview
  addSectionHeaderSlide(
    presentationId,
    'LIVE DEMO'
  );

  addContentSlide(
    presentationId,
    'Building "user-authentication-events" Data Product',
    'We\'ll follow the complete lifecycle:\n\n' +
    'Chapter 1: The Blueprint (with The Architect)\n' +
    'Chapter 2: The Foundation (with The Engineer)\n' +
    'Chapter 3: The Logic (with The Coder)\n' +
    'Chapter 4: The Manual (with The Scribe)\n' +
    'Chapter 5: The Watchtower (with The SRE)\n\n' +
    'Watch how each agent contributes its expertise to build a production-ready data product.'
  );

  // Chapter 1: The Architect
  addBulletSlide(
    presentationId,
    'Chapter 1: The Blueprint',
    [
      '🏗️ Agent: The Architect',
      'Goal: Design the data product schema and contract',
      'Tasks:',
      '  • Recommend schema fields based on use case',
      '  • Identify PII and sensitive data',
      '  • Define SLOs (completeness, latency)',
      '  • Generate formal data contract specification',
      'Output: Data contract ready for engineering'
    ]
  );

  // Chapter 2: The Engineer
  addBulletSlide(
    presentationId,
    'Chapter 2: The Foundation',
    [
      '⚙️ Agent: The Engineer',
      'Goal: Bootstrap project infrastructure',
      'Tasks:',
      '  • Generate Avro schema from contract',
      '  • Create Terraform configs for Kafka topic',
      '  • Scaffold boilerplate Kafka Streams app',
      '  • Configure CI/CD pipeline',
      'Output: Pull Request with complete project structure'
    ]
  );

  // Chapter 3: The Coder
  addBulletSlide(
    presentationId,
    'Chapter 3: The Logic',
    [
      '💻 Agent: The Coder',
      'Goal: Implement business logic and tests',
      'Tasks:',
      '  • Write stream processing filters and transformations',
      '  • Generate unit tests for business logic',
      '  • Create integration tests for Kafka Streams topology',
      '  • Add code documentation',
      'Output: Production-ready application code'
    ]
  );

  // Chapter 4: The Scribe
  addBulletSlide(
    presentationId,
    'Chapter 4: The Manual',
    [
      '📚 Agent: The Scribe',
      'Goal: Document and register the data product',
      'Tasks:',
      '  • Extract schema and ownership from code',
      '  • Identify downstream consumers',
      '  • Generate comprehensive README.md',
      '  • Register in Data Catalog with metadata',
      'Output: Discoverable, well-documented data product'
    ]
  );

  // Chapter 5: The SRE
  addBulletSlide(
    presentationId,
    'Chapter 5: The Watchtower',
    [
      '🔍 Agent: The SRE',
      'Goal: Create observability infrastructure',
      'Tasks:',
      '  • Define key metrics (consumer lag, throughput, errors)',
      '  • Generate Terraform for monitoring dashboards',
      '  • Configure alerts based on SLOs',
      '  • Create runbook for common issues',
      'Output: Full observability from day one'
    ]
  );

  // Demo Transition Slide
  addContentSlide(
    presentationId,
    'Let\'s Watch It In Action',
    '[SWITCH TO LIVE DEMO]\n\n' +
    'Starting prompt:\n\n' +
    '"I need a new data product for user-authentication-events. ' +
    'The schema needs userId, eventTimestamp, ipAddress, userAgent, and loginSuccess (boolean). ' +
    'Tag ipAddress and userAgent as PII. ' +
    'SLOs: 99.9% completeness, 5-second delivery latency."'
  );

  Logger.log('✓ Demo slides complete');
}
