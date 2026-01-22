const MAX_BARS = 50;

async function loadArtistCounts() {
  const response = await fetch("../data/processed/artist_counts.json");
  if (!response.ok) {
    throw new Error(`Failed to load data: ${response.status}`);
  }
  return response.json();
}

function buildChart(entries) {
  const topEntries = entries.slice(0, MAX_BARS);
  const artists = topEntries.map((entry) => entry.artist);
  const counts = topEntries.map((entry) => entry.count);

  const data = [
    {
      type: "bar",
      x: artists,
      y: counts,
      marker: {
        color: "#ec7a5c",
      },
      hovertemplate: "%{x}<br>%{y} tracks<extra></extra>",
    },
  ];

  const layout = {
    margin: { t: 30, r: 20, b: 130, l: 50 },
    xaxis: {
      tickangle: -45,
      automargin: true,
    },
    yaxis: {
      title: "Track count",
    },
    paper_bgcolor: "rgba(0,0,0,0)",
    plot_bgcolor: "rgba(0,0,0,0)",
  };

  Plotly.newPlot("chart", data, layout, { responsive: true });
}

async function init() {
  const chartEl = document.getElementById("chart");
  try {
    const entries = await loadArtistCounts();
    if (!Array.isArray(entries) || entries.length === 0) {
      chartEl.textContent = "No data found. Run python src/build_data.py first.";
      return;
    }
    buildChart(entries);
  } catch (error) {
    chartEl.textContent = `Error: ${error.message}`;
  }
}

init();
