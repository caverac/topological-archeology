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
  { A: 0.0, h1_persistent: 1, h1_max_lifetime: 0.743, h0_max_lifetime: 12.067, h0_gap: 9.595 },
  { A: 0.05, h1_persistent: 1, h1_max_lifetime: 0.504, h0_max_lifetime: 8.227, h0_gap: 5.434 },
  { A: 0.1, h1_persistent: 0, h1_max_lifetime: 0.293, h0_max_lifetime: 4.496, h0_gap: 2.156 },
  { A: 0.15, h1_persistent: 0, h1_max_lifetime: 0.394, h0_max_lifetime: 4.398, h0_gap: 2.328 },
  { A: 0.2, h1_persistent: 2, h1_max_lifetime: 0.566, h0_max_lifetime: 4.48, h0_gap: 2.419 },
  { A: 0.25, h1_persistent: 1, h1_max_lifetime: 0.584, h0_max_lifetime: 2.495, h0_gap: 0.249 },
  { A: 0.3, h1_persistent: 0, h1_max_lifetime: 0.437, h0_max_lifetime: 4.782, h0_gap: 1.192 }
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

    // Glow filter for hover effect
    const defs = svg.append('defs')
    const filter = defs.append('filter').attr('id', 'bar-glow')
    filter.append('feGaussianBlur').attr('stdDeviation', '3').attr('result', 'coloredBlur')
    const feMerge = filter.append('feMerge')
    feMerge.append('feMergeNode').attr('in', 'coloredBlur')
    feMerge.append('feMergeNode').attr('in', 'SourceGraphic')

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

    // Tooltip
    const tooltip = d3
      .select(svgRef.current.parentElement!)
      .append('div')
      .style('position', 'absolute')
      .style('pointer-events', 'none')
      .style('background', 'var(--ifm-background-surface-color, #fff)')
      .style('border', '1px solid var(--ifm-color-emphasis-300, #ccc)')
      .style('border-radius', '6px')
      .style('padding', '8px 12px')
      .style('font-size', '12px')
      .style('line-height', '1.5')
      .style('box-shadow', '0 2px 8px rgba(0,0,0,0.15)')
      .style('opacity', 0)
      .style('transition', 'opacity 0.15s ease')
      .style('z-index', '10')

    // Cleanup tooltip on unmount
    const tooltipNode = tooltip.node()

    // --- H1 persistent count (bars) with hover ---
    const barWidth = w / 14
    const bars = g
      .selectAll<SVGRectElement, DataPoint>('.bar')
      .data(DATA)
      .enter()
      .append('rect')
      .attr('class', 'bar')
      .attr('x', (d) => x(d.A) - barWidth / 2)
      .attr('y', (d) => yLeft(d.h1_persistent))
      .attr('width', barWidth)
      .attr('height', (d) => h - yLeft(d.h1_persistent))
      .attr('fill', 'var(--ifm-color-primary)')
      .attr('opacity', 0.5)
      .attr('rx', 2)
      .style('cursor', 'pointer')
      .style('transition', 'none')

    // H1 persistent count labels
    const barLabels = g
      .selectAll<SVGTextElement, DataPoint>('.bar-label')
      .data(DATA)
      .enter()
      .append('text')
      .attr('class', 'bar-label')
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
    const dots = g
      .selectAll<SVGCircleElement, DataPoint>('.dot')
      .data(DATA)
      .enter()
      .append('circle')
      .attr('class', 'dot')
      .attr('cx', (d) => x(d.A))
      .attr('cy', (d) => yRight(d.h1_max_lifetime))
      .attr('r', 4)
      .attr('fill', '#e67e22')
      .style('cursor', 'pointer')

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

    // --- Invisible wider hit areas for each data point ---
    const hitWidth = w / 7
    g.selectAll<SVGRectElement, DataPoint>('.hit-area')
      .data(DATA)
      .enter()
      .append('rect')
      .attr('class', 'hit-area')
      .attr('x', (d) => x(d.A) - hitWidth / 2)
      .attr('y', 0)
      .attr('width', hitWidth)
      .attr('height', h)
      .attr('fill', 'transparent')
      .style('cursor', 'pointer')
      .on('mouseenter', (_event, d) => {
        const i = DATA.indexOf(d)

        // Bar: glow + scale up
        d3.select(bars.nodes()[i])
          .transition()
          .duration(200)
          .attr('opacity', 0.85)
          .attr('filter', 'url(#bar-glow)')
          .attr('x', x(d.A) - barWidth * 0.65)
          .attr('width', barWidth * 1.3)

        // Bar label: bounce up
        d3.select(barLabels.nodes()[i])
          .transition()
          .duration(200)
          .attr('y', yLeft(d.h1_persistent) - 14)
          .style('font-size', '15px')

        // Dot: pulse bigger
        d3.select(dots.nodes()[i]).transition().duration(200).attr('r', 8).attr('fill', '#f39c12')

        // Show tooltip
        const svgRect = svgRef.current!.getBoundingClientRect()
        const xPos = ((x(d.A) + MARGIN.left) / WIDTH) * svgRect.width
        tooltip
          .html(
            `<strong>A = ${d.A.toFixed(2)}</strong><br/>` +
              `H\u2081 persistent: <strong>${d.h1_persistent}</strong><br/>` +
              `H\u2081 max lifetime: <strong>${d.h1_max_lifetime.toFixed(3)}</strong><br/>` +
              `H\u2080 max lifetime: <strong>${d.h0_max_lifetime.toFixed(3)}</strong><br/>` +
              `H\u2080 gap: <strong>${d.h0_gap.toFixed(3)}</strong>`
          )
          .style('left', `${xPos}px`)
          .style('top', '-10px')
          .style('opacity', 1)
      })
      .on('mouseleave', (_event, d) => {
        const i = DATA.indexOf(d)

        // Bar: restore
        d3.select(bars.nodes()[i])
          .transition()
          .duration(300)
          .attr('opacity', 0.5)
          .attr('filter', null)
          .attr('x', x(d.A) - barWidth / 2)
          .attr('width', barWidth)

        // Bar label: restore
        d3.select(barLabels.nodes()[i])
          .transition()
          .duration(300)
          .attr('y', yLeft(d.h1_persistent) - 6)
          .style('font-size', '12px')

        // Dot: restore
        d3.select(dots.nodes()[i]).transition().duration(300).attr('r', 4).attr('fill', '#e67e22')

        // Hide tooltip
        tooltip.style('opacity', 0)
      })

    return () => {
      if (tooltipNode?.parentElement) {
        tooltipNode.parentElement.removeChild(tooltipNode)
      }
    }
  }, [])

  return (
    <figure className="scientific" style={{ position: 'relative' }}>
      <svg ref={svgRef} style={{ width: '100%', maxWidth: WIDTH, height: 'auto' }} />
      <figcaption>
        Bifurcation diagram: persistent H<sub>1</sub> features (bars, left axis) and maximum H
        <sub>1</sub> lifetime (orange line, right axis) as a function of perturbation amplitude A.
        The dashed line marks the persistence threshold (0.5). The non-monotonic oscillation
        reflects the cosine structure of the density perturbation.{' '}
        <em>Hover over each data point for details.</em>
      </figcaption>
    </figure>
  )
}
