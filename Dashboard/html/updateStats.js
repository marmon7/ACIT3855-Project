/* UPDATE THESE VALUES TO MATCH YOUR SETUP */

const PROCESSING_STATS_API_URL = "http://summerfun.westus.cloudapp.azure.com/processor/stats"
const ANALYZER_API_URL = {
    stats: "http://summerfun.westus.cloudapp.azure.com/analyzer/stats",
    beach_condition: "http://summerfun.westus.cloudapp.azure.com/analyzer/beachcondition",
    book_activity: "http://summerfun.westus.cloudapp.azure.com/analyzer/bookactivity"
}
const CONSISTENCY_API_URL = "http://consistency:8120/consistency"

function triggerConsistencyUpdate() {
    // Perform the POST request using fetch API
    fetch(`${CONSISTENCY_API_URL}/update`, {
        method: 'POST',  // POST request
        headers: {
            'Content-Type': 'application/json',  // Define the content type
        },
    })
    .then(response => response.json())  // Parse the JSON response
    .then(data => {
        alert('Consistency update triggered successfully!');
    })
    .catch(error => {
        // Handle error
        console.error('Error triggering consistency update:', error);
        alert('Failed to trigger consistency update.');
    })
    .then(makeReq(`${CONSISTENCY_API_URL}/checks`, (result) => updateCodeDiv(result, "consistency_update")))
}

// This function fetches and updates the general statistics
const makeReq = (url, cb) => {
    fetch(url)
        .then(res => res.json())
        .then((result) => {
            cb(result);
        }).catch((error) => {
            updateErrorMessages(error.message)
        })
}

const updateCodeDiv = (result, elemId) => document.getElementById(elemId).innerText = JSON.stringify(result)

const getLocaleDateStr = () => (new Date()).toLocaleString()

const getStats = () => {
    document.getElementById("last-updated-value").innerText = getLocaleDateStr()
    totals = {
        num_beach_conditions:1,
        num_summer_activities:1
    }
    makeReq(PROCESSING_STATS_API_URL, (result) => updateCodeDiv(result, "processing-stats"))
    makeReq(ANALYZER_API_URL.stats, (result) => updateCodeDiv(result, "analyzer-stats"))
    try{totals = JSON.parse(document.getElementById("analyzer-stats").innerText)}catch(e){stoperror()}
    makeReq(`${ANALYZER_API_URL.beach_condition}?index=${getRandomInt(0,totals.num_beach_conditions)}`, (result) => updateCodeDiv(result, "event-condition"))
    makeReq(`${ANALYZER_API_URL.book_activity}?index=${getRandomInt(0,totals.num_summer_activities)}`, (result) => updateCodeDiv(result, "event-activity"))
}

const updateErrorMessages = (message) => {
    const id = Date.now()
    console.log("Creation", id)
    msg = document.createElement("div")
    msg.id = `error-${id}`
    msg.innerHTML = `<p>Something happened at ${getLocaleDateStr()}!</p><code>${message}</code>`
    document.getElementById("messages").style.display = "block"
    document.getElementById("messages").prepend(msg)
    setTimeout(() => {
        const elem = document.getElementById(`error-${id}`)
        if (elem) { elem.remove() }
    }, 7000)
}

const setup = () => {
    getStats()
    setInterval(() => getStats(), 4000) // Update every 4 seconds
}

function stoperror() {
    return true;
 }

 function getRandomInt(min, max) {
    const minCeiled = Math.ceil(min);
    const maxFloored = Math.floor(max);
    return Math.floor(Math.random() * (maxFloored - minCeiled) + minCeiled); // The maximum is exclusive and the minimum is inclusive
  }
document.addEventListener('DOMContentLoaded', setup)