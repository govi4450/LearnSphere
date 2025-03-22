const apiKey = "AIzaSyDmlFU86ydq5734N5P_55KeYgKnJHj1GTY"; 
const backendUrl = "http://127.0.0.1:5000";  // Flask backend URL

async function fetchVideos(topic) {
    const url = `https://www.googleapis.com/youtube/v3/search?part=snippet&type=video&q=${encodeURIComponent(topic)}&maxResults=5&key=${apiKey}`;

    try {
        let response = await fetch(url);
        let data = await response.json();
        let videos = data.items;

        let videoIds = videos.map(video => video.id.videoId).join(",");
        let statsUrl = `https://www.googleapis.com/youtube/v3/videos?part=statistics&id=${videoIds}&key=${apiKey}`;
        let statsResponse = await fetch(statsUrl);
        let statsData = await statsResponse.json();

        displayVideos(videos, statsData.items);
    } catch (error) {
        console.error("Error fetching videos:", error);
    }
}

function displayVideos(videos, stats) {
    let container = document.getElementById("videoList");
    container.innerHTML = "";

    videos.forEach((video, index) => {
        let videoId = video.id.videoId;
        let statsInfo = stats.find(stat => stat.id === videoId)?.statistics || {};
        let likes = statsInfo.likeCount || "N/A";
        let views = statsInfo.viewCount || "N/A";

        let li = document.createElement("li");
        li.innerHTML = `
            <div style="display: flex; align-items: center; gap: 10px;">
                <iframe width="560" height="315" src="https://www.youtube.com/embed/${videoId}" frameborder="0" allowfullscreen></iframe>
                <div>
                    <p><strong>Likes:</strong> ${likes}</p>
                    <p><strong>Views:</strong> ${views}</p>
                    <button onclick="summarizeVideo('${videoId}', this)">Summarize</button>
                    <button onclick="viewSummary('${videoId}')">View Summary</button>
                    <ul id="summary-${videoId}" style="margin-top:10px; font-style:italic; color:#333;"></ul>
                </div>
            </div>
        `;
        container.appendChild(li);
    });
}

async function summarizeVideo(videoId, button) {
    let summaryList = document.getElementById(`summary-${videoId}`);
    summaryList.innerHTML = "<li>Checking for saved summary...</li>";
    button.disabled = true;

    try {
        let response = await fetch(`${backendUrl}/summarize?video_id=${videoId}`);
        let data = await response.json();

        if (data.summary && Array.isArray(data.summary)) {
            summaryList.innerHTML = data.summary.map(point => `<li>${point}</li>`).join("");
        } else {
            summaryList.innerHTML = "<li>No summary available.</li>";
        }
    } catch (error) {
        summaryList.innerHTML = "<li>Error fetching summary.</li>";
        console.error("Fetch Error:", error);
    } finally {
        button.disabled = false;
    }
}

function viewSummary(videoId) {
    localStorage.setItem("lastTopic", document.getElementById("searchQuery").value);
    window.location.href = `summary.html?video_id=${videoId}`;
}

function getRecommendations() {
    let topic = document.getElementById("searchQuery").value;
    
    if (topic) {
        localStorage.setItem("lastTopic", topic);
        fetchVideos(topic);
    }
}

// Restore previous search topic & videos when returning
window.onload = function() {
    let savedTopic = localStorage.getItem("lastTopic");
    if (savedTopic) {
        document.getElementById("searchQuery").value = savedTopic;
        fetchVideos(savedTopic);
    }
};
