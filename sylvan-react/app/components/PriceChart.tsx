import React, { useMemo, useRef, useState } from 'react';

export interface PricePoint {
  date: string;
  value: number;
}

const WIDTH = 600;
const HEIGHT = 160;
const MARGIN = { top: 12, right: 12, bottom: 22, left: 48 };
const LINE_COLOUR = '#08c';
const GRID_COLOUR = '#3a3a3a';
const TEXT_COLOUR = '#999';

/**
 * A round step for y-axis ticks that gives about four ticks up to max
 */
function niceStep(max: number): number {
  const rough = max / 4;
  const magnitude = 10 ** Math.floor(Math.log10(rough));
  const residual = rough / magnitude;
  const nice = residual > 5 ? 10 : residual > 2 ? 5 : residual > 1 ? 2 : 1;
  return nice * magnitude;
}

function formatDollars(value: number): string {
  if (value >= 1000) return `$${(value / 1000).toFixed(value >= 10000 ? 0 : 1)}K`;
  return `$${value % 1 === 0 ? value : value.toFixed(2)}`;
}

function formatDate(date: Date): string {
  return date.toLocaleDateString(undefined, { day: 'numeric', month: 'short', year: 'numeric' });
}

/**
 * Line chart of a printing's price over time, with a hover crosshair and a table view
 */
export default function PriceChart({ title, points }: { title: string; points: PricePoint[] }) {
  const svgRef = useRef<SVGSVGElement>(null);
  const [hoverIndex, setHoverIndex] = useState<number | null>(null);

  const chart = useMemo(() => {
    const data = points.map((p) => ({ date: new Date(p.date), value: p.value }));
    const minTime = data[0].date.getTime();
    const maxTime = data[data.length - 1].date.getTime();
    const step = niceStep(Math.max(...data.map((d) => d.value)) || 1);
    const yMax = Math.ceil(Math.max(...data.map((d) => d.value)) / step) * step || step;
    const plotWidth = WIDTH - MARGIN.left - MARGIN.right;
    const plotHeight = HEIGHT - MARGIN.top - MARGIN.bottom;

    const x = (date: Date) =>
      MARGIN.left + ((date.getTime() - minTime) / (maxTime - minTime || 1)) * plotWidth;
    const y = (value: number) => MARGIN.top + plotHeight - (value / yMax) * plotHeight;

    const yTicks: number[] = [];
    for (let v = 0; v <= yMax + step / 2; v += step) yTicks.push(v);

    // First, middle and last dates are enough to place the line in time
    const xTicks = [...new Set([0, Math.floor((data.length - 1) / 2), data.length - 1])];

    const path = data
      .map((d, i) => `${i === 0 ? 'M' : 'L'}${x(d.date).toFixed(1)},${y(d.value).toFixed(1)}`)
      .join(' ');

    return { data, x, y, yTicks, xTicks, path };
  }, [points]);

  function onPointerMove(e: React.PointerEvent<SVGSVGElement>) {
    const svg = svgRef.current;
    if (!svg) return;
    const rect = svg.getBoundingClientRect();
    const pointerX = ((e.clientX - rect.left) / rect.width) * WIDTH;
    let nearest = 0;
    chart.data.forEach((d, i) => {
      if (
        Math.abs(chart.x(d.date) - pointerX) <
        Math.abs(chart.x(chart.data[nearest].date) - pointerX)
      ) {
        nearest = i;
      }
    });
    setHoverIndex(nearest);
  }

  const hovered = hoverIndex !== null ? chart.data[hoverIndex] : null;
  const latest = chart.data[chart.data.length - 1];

  return (
    <figure style={{ margin: '10px 0 0' }}>
      <figcaption className="subtitle" style={{ color: '#ddd' }}>
        <b>{title}</b>
      </figcaption>
      <div style={{ position: 'relative' }}>
        <svg
          ref={svgRef}
          viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
          width="100%"
          role="img"
          aria-label={`${title} from ${formatDate(chart.data[0].date)} to ${formatDate(
            latest.date,
          )}, latest ${formatDollars(latest.value)}`}
          onPointerMove={onPointerMove}
          onPointerLeave={() => setHoverIndex(null)}
          style={{ display: 'block', touchAction: 'none' }}
        >
          {chart.yTicks.map((tick) => (
            <g key={tick}>
              <line
                x1={MARGIN.left}
                x2={WIDTH - MARGIN.right}
                y1={chart.y(tick)}
                y2={chart.y(tick)}
                stroke={GRID_COLOUR}
                strokeWidth={1}
              />
              <text
                x={MARGIN.left - 6}
                y={chart.y(tick)}
                fill={TEXT_COLOUR}
                fontSize={11}
                textAnchor="end"
                dominantBaseline="middle"
              >
                {formatDollars(tick)}
              </text>
            </g>
          ))}
          {chart.xTicks.map((i) => (
            <text
              key={i}
              x={chart.x(chart.data[i].date)}
              y={HEIGHT - 6}
              fill={TEXT_COLOUR}
              fontSize={11}
              textAnchor={i === 0 ? 'start' : i === chart.data.length - 1 ? 'end' : 'middle'}
            >
              {formatDate(chart.data[i].date)}
            </text>
          ))}
          <path
            d={chart.path}
            fill="none"
            stroke={LINE_COLOUR}
            strokeWidth={2}
            strokeLinejoin="round"
            strokeLinecap="round"
          />
          {hovered && (
            <>
              <line
                x1={chart.x(hovered.date)}
                x2={chart.x(hovered.date)}
                y1={MARGIN.top}
                y2={HEIGHT - MARGIN.bottom}
                stroke={TEXT_COLOUR}
                strokeWidth={1}
              />
              <circle
                cx={chart.x(hovered.date)}
                cy={chart.y(hovered.value)}
                r={4}
                fill={LINE_COLOUR}
                stroke="#333"
                strokeWidth={2}
              />
            </>
          )}
        </svg>
        {hovered && (
          <div
            style={{
              position: 'absolute',
              top: 0,
              left: `${(chart.x(hovered.date) / WIDTH) * 100}%`,
              transform: `translateX(${chart.x(hovered.date) > WIDTH / 2 ? 'calc(-100% - 8px)' : '8px'})`,
              background: '#222',
              border: '1px solid #444',
              borderRadius: 3,
              padding: '4px 8px',
              fontSize: 12,
              color: '#ddd',
              whiteSpace: 'nowrap',
              pointerEvents: 'none',
            }}
          >
            <div style={{ color: TEXT_COLOUR }}>{formatDate(hovered.date)}</div>
            <div>{formatDollars(hovered.value)}</div>
          </div>
        )}
      </div>
      <details>
        <summary className="subtitle" style={{ cursor: 'pointer' }}>
          Show price table
        </summary>
        <table className="subtitle">
          <thead>
            <tr>
              <th style={{ textAlign: 'left' }}>Date</th>
              <th style={{ textAlign: 'right' }}>Price</th>
            </tr>
          </thead>
          <tbody>
            {chart.data.map((d) => (
              <tr key={d.date.toISOString()}>
                <td>{formatDate(d.date)}</td>
                <td style={{ textAlign: 'right' }}>${d.value.toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </details>
    </figure>
  );
}
