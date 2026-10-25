import React, { useMemo, useRef, useState } from 'react';

export interface PricePoint {
  date: string;
  value: number;
}

export interface PriceSeries {
  key: string;
  label: string;
  points: PricePoint[];
}

const WIDTH = 600;
const HEIGHT = 160;
const MARGIN = { top: 12, right: 12, bottom: 22, left: 48 };
// Each series keeps its colour by position, whether or not the others are shown
const SERIES_COLOURS = ['#08c', '#d95926'];
const HIDDEN_STORAGE_KEY = 'price-chart-hidden-series';

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

// Which series are hidden is remembered between charts, so hiding foil prices once
// hides them on every card
function loadHidden(): Set<string> {
  try {
    return new Set(JSON.parse(localStorage.getItem(HIDDEN_STORAGE_KEY) ?? '[]'));
  } catch {
    return new Set();
  }
}

function saveHidden(hidden: Set<string>) {
  try {
    localStorage.setItem(HIDDEN_STORAGE_KEY, JSON.stringify([...hidden]));
  } catch {
    // Not being able to remember the choice doesn't matter
  }
}

/**
 * Line chart of a printing's prices over time, with a legend that can hide each line, a
 * hover crosshair and a table view
 */
export default function PriceChart({ title, series }: { title: string; series: PriceSeries[] }) {
  const svgRef = useRef<SVGSVGElement>(null);
  const [hoverTime, setHoverTime] = useState<number | null>(null);
  const [hidden, setHidden] = useState<Set<string>>(loadHidden);

  const allLines = useMemo(
    () =>
      series
        .map((s, i) => ({
          ...s,
          colour: SERIES_COLOURS[i % SERIES_COLOURS.length],
          data: s.points.map((p) => ({ time: new Date(p.date).getTime(), value: p.value })),
        }))
        .filter((line) => line.data.length > 0),
    [series],
  );
  // A remembered choice can hide the only line a printing has prices for, in which case
  // everything is shown rather than an empty chart
  const shownLines = useMemo(
    () =>
      allLines.some((line) => !hidden.has(line.key))
        ? allLines.filter((line) => !hidden.has(line.key))
        : allLines,
    [allLines, hidden],
  );

  const chart = useMemo(() => {
    const times = [...new Set(shownLines.flatMap((line) => line.data.map((d) => d.time)))].sort(
      (a, b) => a - b,
    );
    const minTime = times[0];
    const maxTime = times[times.length - 1];
    const maxValue = Math.max(...shownLines.flatMap((line) => line.data.map((d) => d.value)));
    const step = niceStep(maxValue || 1);
    const yMax = Math.ceil(maxValue / step) * step || step;
    const plotWidth = WIDTH - MARGIN.left - MARGIN.right;
    const plotHeight = HEIGHT - MARGIN.top - MARGIN.bottom;

    // A single date sits in the middle rather than on the left edge
    const x = (time: number) =>
      maxTime === minTime
        ? MARGIN.left + plotWidth / 2
        : MARGIN.left + ((time - minTime) / (maxTime - minTime)) * plotWidth;
    const y = (value: number) => MARGIN.top + plotHeight - (value / yMax) * plotHeight;

    const yTicks: number[] = [];
    for (let v = 0; v <= yMax + step / 2; v += step) yTicks.push(v);

    // First, middle and last dates are enough to place the lines in time
    const xTicks = [
      ...new Set([times[0], times[Math.floor((times.length - 1) / 2)], times[times.length - 1]]),
    ];

    const paths = shownLines.map((line) => ({
      ...line,
      path: line.data
        .map((d, i) => `${i === 0 ? 'M' : 'L'}${x(d.time).toFixed(1)},${y(d.value).toFixed(1)}`)
        .join(' '),
    }));

    return { times, x, y, yTicks, xTicks, paths };
  }, [shownLines]);

  function toggle(key: string) {
    const next = new Set(hidden);
    if (next.has(key)) next.delete(key);
    else next.add(key);
    setHidden(next);
    saveHidden(next);
  }

  function onPointerMove(e: React.PointerEvent<SVGSVGElement>) {
    const svg = svgRef.current;
    if (!svg) return;
    const rect = svg.getBoundingClientRect();
    const pointerX = ((e.clientX - rect.left) / rect.width) * WIDTH;
    let nearest = chart.times[0];
    for (const time of chart.times) {
      if (Math.abs(chart.x(time) - pointerX) < Math.abs(chart.x(nearest) - pointerX)) {
        nearest = time;
      }
    }
    setHoverTime(nearest);
  }

  const hovered =
    hoverTime === null
      ? null
      : chart.paths
          .map((line) => ({ line, point: line.data.find((d) => d.time === hoverTime) }))
          .filter((h) => h.point !== undefined);
  const firstTime = chart.times[0];
  const lastTime = chart.times[chart.times.length - 1];
  const tableTimes = [...new Set(allLines.flatMap((line) => line.data.map((d) => d.time)))].sort(
    (a, b) => a - b,
  );

  return (
    <figure className="price-chart">
      <figcaption className="subtitle price-chart-caption">
        <b>{title}</b>
        {allLines.length > 1 &&
          allLines.map((line) => {
            const shown = shownLines.includes(line);
            // At least one line stays shown
            const onlyShown = shown && shownLines.length === 1;
            return (
              <button
                key={line.key}
                type="button"
                aria-pressed={shown}
                disabled={onlyShown}
                title={
                  shown
                    ? `Hide ${line.label.toLowerCase()} prices`
                    : `Show ${line.label.toLowerCase()} prices`
                }
                onClick={() => toggle(line.key)}
                className="price-chart-legend-button"
              >
                <span
                  aria-hidden="true"
                  className="price-chart-swatch"
                  style={shown ? { background: line.colour } : undefined}
                />
                <span className="price-chart-legend-label">{line.label}</span>
              </button>
            );
          })}
      </figcaption>
      <div className="price-chart-plot">
        <svg
          ref={svgRef}
          viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
          width="100%"
          role="img"
          aria-label={`${title} from ${formatDate(new Date(firstTime))} to ${formatDate(
            new Date(lastTime),
          )}, latest ${chart.paths
            .map((line) => `${line.label} ${formatDollars(line.data[line.data.length - 1].value)}`)
            .join(', ')}`}
          onPointerMove={onPointerMove}
          onPointerLeave={() => setHoverTime(null)}
        >
          {chart.yTicks.map((tick) => (
            <g key={tick}>
              <line
                x1={MARGIN.left}
                x2={WIDTH - MARGIN.right}
                y1={chart.y(tick)}
                y2={chart.y(tick)}
                className="price-chart-grid"
                strokeWidth={1}
              />
              <text
                x={MARGIN.left - 6}
                y={chart.y(tick)}
                className="price-chart-axis"
                fontSize={11}
                textAnchor="end"
                dominantBaseline="middle"
              >
                {formatDollars(tick)}
              </text>
            </g>
          ))}
          {chart.xTicks.map((time) => (
            <text
              key={time}
              x={chart.x(time)}
              y={HEIGHT - 6}
              className="price-chart-axis"
              fontSize={11}
              textAnchor={
                chart.times.length === 1
                  ? 'middle'
                  : time === firstTime
                    ? 'start'
                    : time === lastTime
                      ? 'end'
                      : 'middle'
              }
            >
              {formatDate(new Date(time))}
            </text>
          ))}
          {chart.paths.map((line) => (
            <g key={line.key}>
              <path
                d={line.path}
                fill="none"
                stroke={line.colour}
                strokeWidth={2}
                strokeLinejoin="round"
                strokeLinecap="round"
              />
              {line.data.length === 1 && (
                <circle
                  cx={chart.x(line.data[0].time)}
                  cy={chart.y(line.data[0].value)}
                  r={4}
                  fill={line.colour}
                />
              )}
            </g>
          ))}
          {hoverTime !== null && hovered && (
            <>
              <line
                x1={chart.x(hoverTime)}
                x2={chart.x(hoverTime)}
                y1={MARGIN.top}
                y2={HEIGHT - MARGIN.bottom}
                className="price-chart-crosshair"
                strokeWidth={1}
              />
              {hovered.map(({ line, point }) => (
                <circle
                  key={line.key}
                  cx={chart.x(hoverTime)}
                  cy={chart.y(point!.value)}
                  r={4}
                  fill={line.colour}
                  className="price-chart-hover-point"
                  strokeWidth={2}
                />
              ))}
            </>
          )}
        </svg>
        {hoverTime !== null && hovered && (
          <div
            className="chart-tooltip"
            style={{
              left: `${(chart.x(hoverTime) / WIDTH) * 100}%`,
              transform: `translateX(${chart.x(hoverTime) > WIDTH / 2 ? 'calc(-100% - 8px)' : '8px'})`,
            }}
          >
            <div className="chart-tooltip-date">{formatDate(new Date(hoverTime))}</div>
            {hovered.map(({ line, point }) => (
              <div key={line.key} className="chart-tooltip-row">
                <span
                  aria-hidden="true"
                  className="chart-tooltip-dot"
                  style={{ background: line.colour }}
                />
                {chart.paths.length > 1 && `${line.label}: `}
                {formatDollars(point!.value)}
              </div>
            ))}
          </div>
        )}
      </div>
      <details>
        <summary className="subtitle">Show price table</summary>
        <table className="subtitle price-chart-table">
          <thead>
            <tr>
              <th>Date</th>
              {allLines.map((line) => (
                <th key={line.key}>{allLines.length > 1 ? line.label : 'Price'}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {tableTimes.map((time) => (
              <tr key={time}>
                <td>{formatDate(new Date(time))}</td>
                {allLines.map((line) => {
                  const point = line.data.find((d) => d.time === time);
                  return <td key={line.key}>{point ? `$${point.value.toFixed(2)}` : '–'}</td>;
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </details>
    </figure>
  );
}
