const modal = document.getElementById("country-modal");
const span = document.getElementsByClassName("close")[0];
const zoom = d3.zoom()
    .scaleExtent([1, 15])
    .translateExtent([[0, 0], [2754, 1398]])
    .on('zoom', zoomed);

const svg = d3.select("#map");
svg.call(zoom);

function zoomed() {
    svg
        .selectAll('path')
        .attr('transform', d3.event.transform);
}

for (let country of document.querySelectorAll("#map > g, #map > path")) {
    country.addEventListener('click', async function (e) {
        let data = await getDataByCountryCode(e.currentTarget.id);
        if (!data) return
        modal.style.display = "block";
        for (let elem of document.getElementById("country-modal").querySelectorAll("." + Object.keys(data).join(", ."))) {
            elem.innerHTML = data[elem.className].toLocaleString();
        }
    });
}

async function updateGlobalData() {
    let data = await getDataGlobal();
    for (let elem of document.getElementById("global").querySelectorAll("." + Object.keys(data).join(", ."))) {
        elem.innerHTML = data[elem.className].toLocaleString();
    }
}

span.onclick = function() {
  modal.style.display = "none";
}

window.onclick = function(event) {
  if (event.target == modal) modal.style.display = "none";
}

updateGlobalData();