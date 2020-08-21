const url = "https://api.covid19api.com/summary";

async function getData(url) {
    let r = await fetch(url);
    let data = await r.json();
    return data;
}

async function getDataGlobal() {
    let data = await getData(url);
    return data["Global"];
}

async function getDataByCountryCode(code) {
    let data = await getData(url);
    return data["Countries"].find(country => country["CountryCode"] == code.toUpperCase());
}
