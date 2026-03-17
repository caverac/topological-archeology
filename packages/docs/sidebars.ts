import type { SidebarsConfig } from '@docusaurus/plugin-content-docs'

const sidebars: SidebarsConfig = {
  docsSidebar: [
    'intro',
    {
      type: 'category',
      label: 'Semi-Analytic Simulations',
      items: ['simulations/algorithm', 'simulations/results', 'simulations/runs']
    },
    {
      type: 'category',
      label: 'Topological Data Analysis',
      items: ['tda/preliminaries', 'tda/persistence', 'tda/bifurcation']
    }
  ]
}

export default sidebars
