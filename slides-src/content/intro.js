/**
 * Introduction section slides (~10 minutes)
 */

function addIntroductionSlides(presentationId) {
  Logger.log('Adding introduction slides...');

  // Slide 1: Title Slide
  addTitleSlide(
    presentationId,
    CONFIG.PRESENTATION_TITLE,
    CONFIG.CONFERENCE
  );

  // Slide 2: The Journey Today (Agenda)
  addBulletSlide(
    presentationId,
    'The Journey Today',
    [
      'The Chaos: The pain of modern data platforms',
      'The Promise: What the Data Mesh was supposed to be',
      'The Clarity: An agentic approach to deliver on the promise',
      'The Proof: Live demo - Building a data product end-to-end with AI agents'
    ]
  );

  // Slide 3: Who Am I?
  addBulletSlide(
    presentationId,
    'Who Am I?',
    [
      CONFIG.AUTHOR.name,
      CONFIG.AUTHOR.title + ' at ' + CONFIG.AUTHOR.company,
      'Passionate about making complex data platforms simple for developers',
      'Blog: ' + CONFIG.AUTHOR.blog
    ]
  );

  Logger.log('✓ Introduction slides complete');
}
