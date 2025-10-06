/**
 * Main entry point for building the Data Mesh Agent Team presentation.
 *
 * This script generates a Google Slides presentation programmatically,
 * pulling content from the project's documentation to ensure slides
 * stay in sync with the actual demo implementation.
 */

/**
 * Main function: Builds the complete presentation
 */
function buildPresentation() {
  Logger.log('Starting presentation build...');

  const presentationId = createNewPresentation();

  if (!presentationId) {
    Logger.log('ERROR: Failed to create presentation');
    return;
  }

  Logger.log('Building slides...');

  // Build each section (imported from content modules)
  addIntroductionSlides(presentationId);
  addProblemSlides(presentationId);
  addSolutionSlides(presentationId);
  addDemoSlides(presentationId);
  addConclusionSlides(presentationId);

  const url = 'https://docs.google.com/presentation/d/' + presentationId;
  Logger.log('✅ Presentation complete!');
  Logger.log('View at: ' + url);

  return url;
}

/**
 * Creates a new blank presentation
 * @return {string} The ID of the newly created presentation
 */
function createNewPresentation() {
  try {
    const presentation = SlidesApp.create(CONFIG.PRESENTATION_TITLE);
    const presentationId = presentation.getId();

    Logger.log('Created presentation: ' + presentationId);
    return presentationId;

  } catch (error) {
    Logger.log('Error creating presentation: ' + error);
    return null;
  }
}

/**
 * Helper function: Add a title slide (large title + subtitle)
 */
function addTitleSlide(presentationId, title, subtitle) {
  const requests = [{
    createSlide: {
      slideLayoutReference: {
        predefinedLayout: 'TITLE'
      }
    }
  }];

  const response = Slides.Presentations.batchUpdate({
    requests: requests
  }, presentationId);

  const slideId = response.replies[0].createSlide.objectId;

  // Add text to the slide
  const presentation = Slides.Presentations.get(presentationId);
  const slide = presentation.slides.find(s => s.objectId === slideId);

  const textRequests = [];

  const titlePlaceholder = slide.pageElements.find(
    el => el.shape && el.shape.placeholder &&
    (el.shape.placeholder.type === 'CENTERED_TITLE' || el.shape.placeholder.type === 'TITLE')
  );

  const subtitlePlaceholder = slide.pageElements.find(
    el => el.shape && el.shape.placeholder && el.shape.placeholder.type === 'SUBTITLE'
  );

  if (titlePlaceholder) {
    textRequests.push({
      insertText: {
        objectId: titlePlaceholder.objectId,
        text: title
      }
    });
  }

  if (subtitlePlaceholder && subtitle) {
    textRequests.push({
      insertText: {
        objectId: subtitlePlaceholder.objectId,
        text: subtitle
      }
    });
  }

  if (textRequests.length > 0) {
    Slides.Presentations.batchUpdate({
      requests: textRequests
    }, presentationId);
  }

  return slideId;
}

/**
 * Helper function: Add a slide with title and body content
 */
function addContentSlide(presentationId, title, bodyText) {
  const requests = [{
    createSlide: {
      slideLayoutReference: {
        predefinedLayout: 'TITLE_AND_BODY'
      }
    }
  }];

  const response = Slides.Presentations.batchUpdate({
    requests: requests
  }, presentationId);

  const slideId = response.replies[0].createSlide.objectId;

  // Add text
  const presentation = Slides.Presentations.get(presentationId);
  const slide = presentation.slides.find(s => s.objectId === slideId);

  const textRequests = [];

  const titlePlaceholder = slide.pageElements.find(
    el => el.shape && el.shape.placeholder && el.shape.placeholder.type === 'TITLE'
  );

  const bodyPlaceholder = slide.pageElements.find(
    el => el.shape && el.shape.placeholder && el.shape.placeholder.type === 'BODY'
  );

  if (titlePlaceholder) {
    textRequests.push({
      insertText: {
        objectId: titlePlaceholder.objectId,
        text: title
      }
    });
  }

  if (bodyPlaceholder && bodyText) {
    textRequests.push({
      insertText: {
        objectId: bodyPlaceholder.objectId,
        text: bodyText
      }
    });
  }

  if (textRequests.length > 0) {
    Slides.Presentations.batchUpdate({
      requests: textRequests
    }, presentationId);
  }

  return slideId;
}

/**
 * Helper function: Add a bullet list slide
 */
function addBulletSlide(presentationId, title, bullets) {
  const bodyText = bullets.join('\n');
  return addContentSlide(presentationId, title, bodyText);
}

/**
 * Helper function: Add a blank slide for custom layouts
 */
function addBlankSlide(presentationId) {
  const requests = [{
    createSlide: {
      slideLayoutReference: {
        predefinedLayout: 'BLANK'
      }
    }
  }];

  const response = Slides.Presentations.batchUpdate({
    requests: requests
  }, presentationId);

  return response.replies[0].createSlide.objectId;
}

/**
 * Helper function: Add a section header slide (big bold text)
 */
function addSectionHeaderSlide(presentationId, headerText) {
  const requests = [{
    createSlide: {
      slideLayoutReference: {
        predefinedLayout: 'SECTION_HEADER'
      }
    }
  }];

  const response = Slides.Presentations.batchUpdate({
    requests: requests
  }, presentationId);

  const slideId = response.replies[0].createSlide.objectId;

  // Add the header text
  const presentation = Slides.Presentations.get(presentationId);
  const slide = presentation.slides.find(s => s.objectId === slideId);

  const titlePlaceholder = slide.pageElements.find(
    el => el.shape && el.shape.placeholder && el.shape.placeholder.type === 'TITLE'
  );

  if (titlePlaceholder) {
    Slides.Presentations.batchUpdate({
      requests: [{
        insertText: {
          objectId: titlePlaceholder.objectId,
          text: headerText
        }
      }]
    }, presentationId);
  }

  return slideId;
}

/**
 * Helper function: Add a two-column slide
 */
function addTwoColumnSlide(presentationId, title, leftContent, rightContent) {
  // For now, create as a title and body slide with formatted text
  // TODO: Create actual two-column layout with custom shapes
  const bodyText = leftContent + '\n\n' + rightContent;
  return addContentSlide(presentationId, title, bodyText);
}
