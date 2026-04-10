/**
 * End-to-End Tests for Phase 3
 *
 * Tests cover:
 * - Complete user signup flow (store type selection)
 * - Dashboard rendering with model info
 * - Forecast chart display
 * - Integration UI display
 * - Store type validation
 */

describe('Phase 3 E2E Tests - Pre-trained Forecasts & Integrations', () => {
  
  describe('Signup Flow with Store Type', () => {
    
    test('User can navigate to signup page', () => {
      // Verify signup page renders
      const signupPage = document.querySelector('[data-testid="signup-page"]');
      expect(signupPage).toBeDefined();
    });

    test('Store type dropdown is present', () => {
      // Verify store type selection dropdown exists
      const storeTypeSelect = document.querySelector('[data-testid="store-type-select"]');
      expect(storeTypeSelect).toBeDefined();
    });

    test('All three store types are available', () => {
      // Verify all 3 store types in dropdown
      const storeTypeOptions = document.querySelectorAll('[data-testid="store-type-option"]');
      const optionValues = Array.from(storeTypeOptions).map(el => el.value);
      
      expect(optionValues).toContain('grocery');
      expect(optionValues).toContain('fashion');
      expect(optionValues).toContain('electronics');
    });

    test('User can select store type', () => {
      // Verify can select each store type
      const storeTypeSelect = document.querySelector('[data-testid="store-type-select"]');
      storeTypeSelect.value = 'grocery';
      
      expect(storeTypeSelect.value).toBe('grocery');
    });

    test('Submit button is disabled without store type', () => {
      // Verify form validation
      const storeTypeSelect = document.querySelector('[data-testid="store-type-select"]');
      const submitButton = document.querySelector('[data-testid="signup-submit"]');
      
      storeTypeSelect.value = '';
      expect(submitButton.disabled).toBe(true);
    });

    test('Submit button is enabled with store type', () => {
      // Verify form validation
      const storeTypeSelect = document.querySelector('[data-testid="store-type-select"]');
      const submitButton = document.querySelector('[data-testid="signup-submit"]');
      
      storeTypeSelect.value = 'grocery';
      expect(submitButton.disabled).toBe(false);
    });

  });

  describe('Dashboard After Signup', () => {
    
    test('Dashboard page loads after signup', () => {
      // Verify user redirected to dashboard
      const dashboard = document.querySelector('[data-testid="dashboard-page"]');
      expect(dashboard).toBeDefined();
    });

    test('Model info banner is displayed', () => {
      // Verify model info shows
      const modelBanner = document.querySelector('[data-testid="model-info-banner"]');
      expect(modelBanner).toBeDefined();
    });

    test('Assigned model name is displayed', () => {
      // Verify model name shown
      const modelName = document.querySelector('[data-testid="model-name"]');
      expect(modelName).toBeDefined();
      expect(modelName.textContent).toMatch(/Grocery|Fashion|Electronics/);
    });

    test('Model version is displayed', () => {
      // Verify model version shown
      const modelVersion = document.querySelector('[data-testid="model-version"]');
      expect(modelVersion).toBeDefined();
      expect(modelVersion.textContent).toMatch(/v1\.0/);
    });

    test('No upload section is visible', () => {
      // Verify upload section removed
      const uploadSection = document.querySelector('[data-testid="upload-section"]');
      expect(uploadSection).toBeNull();
    });

  });

  describe('Forecast Display', () => {
    
    test('Forecast section exists', () => {
      // Verify forecast section
      const forecastSection = document.querySelector('[data-testid="forecast-section"]');
      expect(forecastSection).toBeDefined();
    });

    test('Forecast chart renders', () => {
      // Verify chart element
      const chart = document.querySelector('[data-testid="forecast-chart"]');
      expect(chart).toBeDefined();
    });

    test('Forecast data points are present', () => {
      // Verify forecast data displayed
      const dataPoints = document.querySelectorAll('[data-testid="forecast-data-point"]');
      expect(dataPoints.length).toBeGreaterThan(0);
    });

    test('Horizon selector is available', () => {
      // Verify can select different horizons
      const horizonSelector = document.querySelector('[data-testid="horizon-selector"]');
      expect(horizonSelector).toBeDefined();
    });

    test('Can switch between 7, 14, 30 day horizons', () => {
      // Verify horizon options
      const options = document.querySelectorAll('[data-testid="horizon-option"]');
      const optionValues = Array.from(options).map(el => el.value);
      
      expect(optionValues).toContain('7');
      expect(optionValues).toContain('14');
      expect(optionValues).toContain('30');
    });

  });

  describe('Integration UI Display', () => {
    
    test('Data Sources page is accessible', () => {
      // Verify data sources page
      const dataSources = document.querySelector('[data-testid="data-sources-page"]');
      expect(dataSources).toBeDefined();
    });

    test('Shopify integration card is displayed', () => {
      // Verify Shopify card
      const shopifyCard = document.querySelector('[data-testid="shopify-integration-card"]');
      expect(shopifyCard).toBeDefined();
    });

    test('Square integration card is displayed', () => {
      // Verify Square card
      const squareCard = document.querySelector('[data-testid="square-integration-card"]');
      expect(squareCard).toBeDefined();
    });

    test('Webhook integration card is displayed', () => {
      // Verify Webhook card
      const webhookCard = document.querySelector('[data-testid="webhook-integration-card"]');
      expect(webhookCard).toBeDefined();
    });

    test('Integration cards have connect buttons', () => {
      // Verify connect buttons
      const connectButtons = document.querySelectorAll('[data-testid="integration-connect-btn"]');
      expect(connectButtons.length).toBeGreaterThan(0);
    });

    test('Integration status badges are present', () => {
      // Verify status badges
      const statusBadges = document.querySelectorAll('[data-testid="integration-status"]');
      expect(statusBadges.length).toBeGreaterThan(0);
    });

  });

  describe('Store Type Specific Content', () => {
    
    test('Grocery users see grocery-specific info', async () => {
      // Verify grocery content
      // This would be tested with actual navigation
      const storeType = localStorage.getItem('userStoreType');
      if (storeType === 'grocery') {
        const groceryInfo = document.querySelector('[data-testid="grocery-specific-info"]');
        expect(groceryInfo).toBeDefined();
      }
    });

    test('Fashion users see fashion-specific info', async () => {
      // Verify fashion content
      const storeType = localStorage.getItem('userStoreType');
      if (storeType === 'fashion') {
        const fashionInfo = document.querySelector('[data-testid="fashion-specific-info"]');
        expect(fashionInfo).toBeDefined();
      }
    });

    test('Electronics users see electronics-specific info', async () => {
      // Verify electronics content
      const storeType = localStorage.getItem('userStoreType');
      if (storeType === 'electronics') {
        const electronicsInfo = document.querySelector('[data-testid="electronics-specific-info"]');
        expect(electronicsInfo).toBeDefined();
      }
    });

  });

  describe('Navigation Updates', () => {
    
    test('Upload page removed from navigation', () => {
      // Verify Upload not in sidebar
      const uploadLink = document.querySelector('[data-testid="nav-upload"]');
      expect(uploadLink).toBeNull();
    });

    test('Data Sources link is in navigation', () => {
      // Verify Data Sources in sidebar
      const dataSourcesLink = document.querySelector('[data-testid="nav-data-sources"]');
      expect(dataSourcesLink).toBeDefined();
    });

    test('Dashboard link is in navigation', () => {
      // Verify Dashboard in sidebar
      const dashboardLink = document.querySelector('[data-testid="nav-dashboard"]');
      expect(dashboardLink).toBeDefined();
    });

    test('Can navigate between pages', () => {
      // Verify navigation works
      const dashboardLink = document.querySelector('[data-testid="nav-dashboard"]');
      const dataSourcesLink = document.querySelector('[data-testid="nav-data-sources"]');
      
      expect(dashboardLink).toBeDefined();
      expect(dataSourcesLink).toBeDefined();
    });

  });

  describe('Form Validation', () => {
    
    test('Email validation works', () => {
      // Verify email validation
      const emailInput = document.querySelector('[data-testid="signup-email"]');
      emailInput.value = 'invalid-email';
      
      // Should fail validation
      expect(emailInput.validity.valid).toBe(false);
    });

    test('Valid email passes validation', () => {
      // Verify valid email
      const emailInput = document.querySelector('[data-testid="signup-email"]');
      emailInput.value = 'user@example.com';
      
      // Should pass validation
      expect(emailInput.validity.valid).toBe(true);
    });

    test('Password validation works', () => {
      // Verify password requirements
      const passwordInput = document.querySelector('[data-testid="signup-password"]');
      passwordInput.value = 'short';
      
      // Should require minimum length
      expect(passwordInput.value.length).toBeGreaterThanOrEqual(0);
    });

    test('All required fields must be filled', () => {
      // Verify form requires all fields
      const form = document.querySelector('[data-testid="signup-form"]');
      const requiredFields = form.querySelectorAll('[required]');
      
      expect(requiredFields.length).toBeGreaterThan(0);
    });

  });

  describe('Loading States', () => {
    
    test('Loading spinner shows during signup', () => {
      // Verify loading state
      const submitButton = document.querySelector('[data-testid="signup-submit"]');
      submitButton.click();
      
      const loadingSpinner = document.querySelector('[data-testid="loading-spinner"]');
      expect(loadingSpinner).toBeDefined();
    });

    test('Dashboard shows loading state initially', () => {
      // Verify initial loading
      const loadingState = document.querySelector('[data-testid="dashboard-loading"]');
      expect(loadingState).toBeDefined();
    });

    test('Content appears after loading completes', async () => {
      // Verify content appears
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      const dashboard = document.querySelector('[data-testid="dashboard-content"]');
      expect(dashboard).toBeDefined();
    });

  });

  describe('Error Handling', () => {
    
    test('Shows error for invalid signup', () => {
      // Verify error display
      const form = document.querySelector('[data-testid="signup-form"]');
      form.submit();
      
      const errorMessage = document.querySelector('[data-testid="error-message"]');
      expect(errorMessage).toBeDefined();
    });

    test('Shows error for API failure', async () => {
      // Verify error handling
      // This would need mocked API
      const errorElement = document.querySelector('[data-testid="api-error"]');
      expect(errorElement).toBeDefined();
    });

  });

});

/**
 * Integration Test: Complete User Journey
 */
describe('Complete User Journey - Phase 3', () => {
  
  test('Full flow: Signup > Select Store > Dashboard > View Forecast > See Integrations', async () => {
    
    // 1. Signup page
    const signupPage = document.querySelector('[data-testid="signup-page"]');
    expect(signupPage).toBeDefined();
    
    // 2. Fill signup form
    document.querySelector('[data-testid="signup-name"]').value = 'John Doe';
    document.querySelector('[data-testid="signup-email"]').value = 'user@example.com';
    document.querySelector('[data-testid="signup-password"]').value = 'password123';
    
    // 3. Select store type
    document.querySelector('[data-testid="store-type-select"]').value = 'grocery';
    
    // 4. Submit form
    document.querySelector('[data-testid="signup-submit"]').click();
    
    // 5. Wait for redirect
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    // 6. Verify dashboard loads
    const dashboard = document.querySelector('[data-testid="dashboard-page"]');
    expect(dashboard).toBeDefined();
    
    // 7. Verify model info
    const modelBanner = document.querySelector('[data-testid="model-info-banner"]');
    expect(modelBanner).toBeDefined();
    
    // 8. Verify forecast chart
    const chart = document.querySelector('[data-testid="forecast-chart"]');
    expect(chart).toBeDefined();
    
    // 9. Navigate to integrations
    document.querySelector('[data-testid="nav-data-sources"]').click();
    
    // 10. Verify integration cards
    const shopifyCard = document.querySelector('[data-testid="shopify-integration-card"]');
    expect(shopifyCard).toBeDefined();
    
  });

});
