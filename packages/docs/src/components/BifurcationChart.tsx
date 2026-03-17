import * as d3 from 'd3'
import React, { useEffect, useRef } from 'react'

interface DataPoint {
  A: number
  h1_persistent: number
  h1_max_lifetime: number
  h0_max_lifetime: number
  h0_gap: number
}

const DATA: DataPoint[] = [
  { A: 0.0, h1_persistent: 3, h1_max_lifetime: 0.889, h0_max_lifetime: 4.5, h0_gap: 1.922 },
  { A: 0.05, h1_persistent: 4, h1_max_lifetime: 0.7, h0_max_lifetime: 2.496, h0_gap: 0.102 },
  { A: 0.1, h1_persistent: 1, h1_max_lifetime: 0.52, h0_max_lifetime: 4.021, h0_gap: 1.012 },
  { A: 0.15, h1_persistent: 0, h1_max_lifetime: 0.485, h0_max_lifetime: 2.528, h0_gap: 0.164 },
  { A: 0.2, h1_persistent: 2, h1_max_lifetime: 0.734, h0_max_lifetime: 3.968, h0_gap: 1.205 },
  { A: 0.25, h1_persistent: 0, h1_max_lifetime: 0.484, h0_max_lifetime: 6.179, h0_gap: 2.548 },
  { A: 0.3, h1_persistent: 2, h1_max_lifetime: 0.576, h0_max_lifetime: 3.638, h0_gap: 0.159 }
]

const MARGIN = { top: 30, right: 60, bottom: 50, left: 60 }
const WIDTH = 640
const HEIGHT = 320

export function BifurcationChart(): React.ReactElement {
  const svgRef = useRef<SVGSVGElement>(null)

  useEffect(() => {
    if (!svgRef.current) return

    const svg = d3.select(svgRef.current)
    svg.selectAll('*').remove()

    const w = WIDTH - MARGIN.left - MARGIN.right
    const h = HEIGHT - MARGIN.top - MARGIN.bottom

    const g = svg
      .attr('viewBox', `0 0 ${WIDTH} ${HEIGHT}`)
      .append('g')
      .attr('transform', `translate(${MARGIN.left},${MARGIN.top})`)

    // Scales
    const x = d3.scaleLinear().domain([0, 0.32]).range([0, w])
    const yLeft = d3.scaleLinear().domain([0, 5]).range([h, 0])
    const yRight = d3.scaleLinear().domain([0, 1.0]).range([h, 0])

    // Axes
    g.append('g')
      .attr('transform', `translate(0,${h})`)
      .call(d3.axisBottom(x).tickValues([0, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3]))
      .selectAll('text')
      .style('font-size', '11px')

    g.append('g').call(d3.axisLeft(yLeft).ticks(5)).selectAll('text').style('font-size', '11px')

    g.append('g')
      .attr('transform', `translate(${w},0)`)
      .call(d3.axisRight(yRight).ticks(5))
      .selectAll('text')
      .style('font-size', '11px')

    // Axis labels
    g.append('text')
      .attr('x', w / 2)
      .attr('y', h + 40)
      .attr('text-anchor', 'middle')
      .style('font-size', '13px')
      .text('Perturbation amplitude A')

    g.append('text')
      .attr('transform', 'rotate(-90)')
      .attr('x', -h / 2)
      .attr('y', -45)
      .attr('text-anchor', 'middle')
      .style('font-size', '13px')
      .style('fill', 'var(--ifm-color-primary)')
      .text('H\u2081 persistent features')

    g.append('text')
      .attr('transform', 'rotate(90)')
      .attr('x', h / 2)
      .attr('y', -w - 45)
      .attr('text-anchor', 'middle')
      .style('font-size', '13px')
      .style('fill', '#e67e22')
      .text('H\u2081 max lifetime')

    // H1 persistent count (bars)
    const barWidth = w / 14
    g.selectAll('.bar')
      .data(DATA)
      .enter()
      .append('rect')
      .attr('x', (d) => x(d.A) - barWidth / 2)
      .attr('y', (d) => yLeft(d.h1_persistent))
      .attr('width', barWidth)
      .attr('height', (d) => h - yLeft(d.h1_persistent))
      .attr('fill', 'var(--ifm-color-primary)')
      .attr('opacity', 0.5)
      .attr('rx', 2)

    // H1 persistent count labels
    g.selectAll('.bar-label')
      .data(DATA)
      .enter()
      .append('text')
      .attr('x', (d) => x(d.A))
      .attr('y', (d) => yLeft(d.h1_persistent) - 6)
      .attr('text-anchor', 'middle')
      .style('font-size', '12px')
      .style('font-weight', '600')
      .style('fill', 'var(--ifm-color-primary)')
      .text((d) => d.h1_persistent)

    // H1 max lifetime line
    const line = d3
      .line<DataPoint>()
      .x((d) => x(d.A))
      .y((d) => yRight(d.h1_max_lifetime))
      .curve(d3.curveMonotoneX)

    g.append('path')
      .datum(DATA)
      .attr('fill', 'none')
      .attr('stroke', '#e67e22')
      .attr('stroke-width', 2.5)
      .attr('d', line)

    // H1 max lifetime dots
    g.selectAll('.dot')
      .data(DATA)
      .enter()
      .append('circle')
      .attr('cx', (d) => x(d.A))
      .attr('cy', (d) => yRight(d.h1_max_lifetime))
      .attr('r', 4)
      .attr('fill', '#e67e22')

    // Threshold line at 0.5
    g.append('line')
      .attr('x1', 0)
      .attr('x2', w)
      .attr('y1', yRight(0.5))
      .attr('y2', yRight(0.5))
      .attr('stroke', '#888')
      .attr('stroke-dasharray', '4,4')
      .attr('stroke-width', 1)

    g.append('text')
      .attr('x', w - 4)
      .attr('y', yRight(0.5) - 5)
      .attr('text-anchor', 'end')
      .style('font-size', '10px')
      .style('fill', '#888')
      .text('threshold = 0.5')
  }, [])

  return (
    <figure className="scientific">
      <svg ref={svgRef} style={{ width: '100%', maxWidth: WIDTH, height: 'auto' }} />
      <figcaption>
        Bifurcation diagram: persistent H<sub>1</sub> features (bars, left axis) and maximum H
        <sub>1</sub> lifetime (orange line, right axis) as a function of perturbation amplitude A.
        The dashed line marks the persistence threshold (0.5). The non-monotonic oscillation
        reflects the cosine structure of the density perturbation.
      </figcaption>
    </figure>
  )
}
