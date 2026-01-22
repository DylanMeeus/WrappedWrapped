const MAX_BARS = 80;

async function loadJson(path) {
  const response = await fetch(path);
  if (!response.ok) {
    throw new Error(`Failed to load data: ${response.status}`);
  }
  return response.json();
}

function buildChart({ entries, valueKey, containerId }) {
  const container = document.querySelector(`#${containerId} .chart-scroll`);
  const svg = d3.select(`#${containerId} .chart-svg`);
  const width = Math.max(900, entries.length * 20);
  const height = 380;
  const margin = { top: 20, right: 20, bottom: 120, left: 50 };

  svg.selectAll("*").remove();
  svg.attr("width", width).attr("height", height);

  const x = d3
    .scaleBand()
    .domain(entries.map((entry) => entry.artist))
    .range([margin.left, width - margin.right])
    .padding(0.2);

  const y = d3
    .scaleLinear()
    .domain([0, d3.max(entries, (entry) => entry[valueKey]) || 0])
    .nice()
    .range([height - margin.bottom, margin.top]);

  svg
    .append("g")
    .attr("class", "axis axis-x")
    .attr("transform", `translate(0,${height - margin.bottom})`)
    .call(d3.axisBottom(x).tickSizeOuter(0))
    .selectAll("text")
    .attr("transform", "rotate(-45)")
    .style("text-anchor", "end");

  svg
    .append("g")
    .attr("class", "axis axis-y")
    .attr("transform", `translate(${margin.left},0)`)
    .call(d3.axisLeft(y).ticks(6));

  svg
    .append("g")
    .selectAll("rect")
    .data(entries)
    .join("rect")
    .attr("x", (entry) => x(entry.artist))
    .attr("y", (entry) => y(entry[valueKey]))
    .attr("height", (entry) => y(0) - y(entry[valueKey]))
    .attr("width", x.bandwidth())
    .attr("rx", 4)
    .attr("fill", "#e07a5f")
    .append("title")
    .text((entry) => `${entry.artist}: ${entry[valueKey]}`);

  container.scrollLeft = 0;
}

async function init() {
  const trackChart = document.getElementById("track-chart");
  const yearChart = document.getElementById("year-chart");

  try {
    const [artistCounts, artistYearCounts] = await Promise.all([
      loadJson("../data/processed/artist_counts.json"),
      loadJson("../data/processed/artist_year_counts.json"),
    ]);

    if (!Array.isArray(artistCounts) || artistCounts.length === 0) {
      trackChart.textContent = "No data found. Run python src/build_data.py first.";
      return;
    }

    if (!Array.isArray(artistYearCounts) || artistYearCounts.length === 0) {
      yearChart.textContent = "No year data found. Run python src/build_data.py first.";
      return;
    }

    buildChart({
      entries: artistCounts.slice(0, MAX_BARS),
      valueKey: "count",
      containerId: "track-chart",
    });

    buildChart({
      entries: artistYearCounts.slice(0, MAX_BARS),
      valueKey: "year_count",
      containerId: "year-chart",
    });
  } catch (error) {
    trackChart.textContent = `Error: ${error.message}`;
  }
}

init();
