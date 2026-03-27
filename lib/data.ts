export const PRODUCTS = {
  Spectrum: {
    titles: ['Finance Director', 'CFO', 'CAO / City Manager', 'Controller', 'IT Director', 'Budget Manager'],
    pain: 'Outdated legacy ERP causing reporting delays, manual reconciliation, lack of integration between finance and HR modules, difficulty producing consolidated budget reports.',
  },
  TRIO: {
    titles: ['Building Official', 'IT Director', 'City Clerk', 'Director of Planning', 'Code Enforcement Manager', 'Director of Community Development'],
    pain: 'Paper-based permitting workflows, no online permit applications, slow inspection scheduling, difficulty tracking code violation cases.',
  },
  MSI: {
    titles: ['City Treasurer', 'Tax Collector', 'Revenue Manager', 'Finance Director', 'Assessor', 'Director of Finance'],
    pain: 'Disconnected tax billing and payment systems, difficulty reconciling revenue across sources, manual batch processing, poor taxpayer self-service.',
  },
  Aurora: {
    titles: ['Utility Director', 'IT Director', 'Finance Director', 'Public Works Director', 'Customer Service Manager', 'CAO'],
    pain: 'Aging utility billing platform, high call volume from billing errors, no self-service payment portal, difficulty integrating AMI meter data.',
  },
} as const

export const CA_PROVINCES = [
  { code: 'AB', name: 'Alberta' }, { code: 'BC', name: 'British Columbia' },
  { code: 'MB', name: 'Manitoba' }, { code: 'NB', name: 'New Brunswick' },
  { code: 'NL', name: 'Newfoundland' }, { code: 'NS', name: 'Nova Scotia' },
  { code: 'NT', name: 'Northwest Territories' }, { code: 'NU', name: 'Nunavut' },
  { code: 'ON', name: 'Ontario' }, { code: 'PE', name: 'PEI' },
  { code: 'QC', name: 'Quebec' }, { code: 'SK', name: 'Saskatchewan' },
  { code: 'YT', name: 'Yukon' },
]

export const US_STATES = [
  { code: 'AL', name: 'Alabama' }, { code: 'AK', name: 'Alaska' }, { code: 'AZ', name: 'Arizona' },
  { code: 'AR', name: 'Arkansas' }, { code: 'CA', name: 'California' }, { code: 'CO', name: 'Colorado' },
  { code: 'CT', name: 'Connecticut' }, { code: 'DE', name: 'Delaware' }, { code: 'FL', name: 'Florida' },
  { code: 'GA', name: 'Georgia' }, { code: 'HI', name: 'Hawaii' }, { code: 'ID', name: 'Idaho' },
  { code: 'IL', name: 'Illinois' }, { code: 'IN', name: 'Indiana' }, { code: 'IA', name: 'Iowa' },
  { code: 'KS', name: 'Kansas' }, { code: 'KY', name: 'Kentucky' }, { code: 'LA', name: 'Louisiana' },
  { code: 'ME', name: 'Maine' }, { code: 'MD', name: 'Maryland' }, { code: 'MA', name: 'Massachusetts' },
  { code: 'MI', name: 'Michigan' }, { code: 'MN', name: 'Minnesota' }, { code: 'MS', name: 'Mississippi' },
  { code: 'MO', name: 'Missouri' }, { code: 'MT', name: 'Montana' }, { code: 'NE', name: 'Nebraska' },
  { code: 'NV', name: 'Nevada' }, { code: 'NH', name: 'New Hampshire' }, { code: 'NJ', name: 'New Jersey' },
  { code: 'NM', name: 'New Mexico' }, { code: 'NY', name: 'New York' }, { code: 'NC', name: 'North Carolina' },
  { code: 'ND', name: 'North Dakota' }, { code: 'OH', name: 'Ohio' }, { code: 'OK', name: 'Oklahoma' },
  { code: 'OR', name: 'Oregon' }, { code: 'PA', name: 'Pennsylvania' }, { code: 'RI', name: 'Rhode Island' },
  { code: 'SC', name: 'South Carolina' }, { code: 'SD', name: 'South Dakota' }, { code: 'TN', name: 'Tennessee' },
  { code: 'TX', name: 'Texas' }, { code: 'UT', name: 'Utah' }, { code: 'VT', name: 'Vermont' },
  { code: 'VA', name: 'Virginia' }, { code: 'WA', name: 'Washington' }, { code: 'WV', name: 'West Virginia' },
  { code: 'WI', name: 'Wisconsin' }, { code: 'WY', name: 'Wyoming' },
]

export const POP_LABELS = ['1k', '2.5k', '5k', '10k', '25k', '50k', '75k', '100k', '150k', '250k', '500k', '500k+']
