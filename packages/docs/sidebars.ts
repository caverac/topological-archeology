import type { SidebarsConfig } from '@docusaurus/plugin-content-docs'

const sidebars: SidebarsConfig = {
  docsSidebar: [
    'intro',
    {
      type: 'category',
      label: 'Semi-Analytic Simulations',
      items: ['simulations/algorithm', 'simulations/results']
    }
  ]
}

export default sidebars
