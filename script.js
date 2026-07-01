const navShell = document.querySelector(".nav-shell");
const navToggle = document.querySelector(".nav-toggle");
const tabs = document.querySelectorAll(".tab");
const bars = document.querySelector("#demo-bars");
const demoTitle = document.querySelector("#demo-title");
const demoDescription = document.querySelector("#demo-description");
const demoTime = document.querySelector("#demo-time");
const demoSpace = document.querySelector("#demo-space");
const practiceForm = document.querySelector("#practice-form");
const topicSelect = document.querySelector("#topic-select");
const challenge = document.querySelector("#challenge");

const demos = {
  binary: {
    title: "Binary Search",
    description: "Repeatedly cut a sorted search space in half by comparing the middle value with the target.",
    time: "Time O(log n)",
    space: "Space O(1)",
    values: [12, 24, 37, 45, 58, 63, 77],
    highlights: [3],
    muted: [0, 1, 5, 6],
  },
  bfs: {
    title: "Breadth-First Search",
    description: "Visit nodes level by level with a queue, making BFS ideal for shortest paths in unweighted graphs.",
    time: "Time O(V + E)",
    space: "Space O(V)",
    values: [1, 2, 2, 3, 3, 3, 3],
    highlights: [1, 2],
    muted: [],
  },
  dp: {
    title: "Dynamic Programming",
    description: "Store answers to smaller overlapping subproblems so each state is solved once and reused later.",
    time: "Time O(n)",
    space: "Space O(n)",
    values: [1, 1, 2, 3, 5, 8, 13],
    highlights: [4, 5, 6],
    muted: [0, 1],
  },
};

const drills = {
  arrays: [
    "Find the longest substring without repeating characters.",
    "Return all triplets in an array that sum to zero.",
    "Find the minimum size subarray with sum at least target.",
  ],
  hashing: [
    "Group strings that are anagrams of each other.",
    "Find the first recurring value in a stream of numbers.",
    "Count subarrays with a sum equal to k.",
  ],
  trees: [
    "Validate whether a binary tree is a binary search tree.",
    "Return the lowest common ancestor of two nodes.",
    "Find the maximum path sum in a binary tree.",
  ],
  graphs: [
    "Detect whether a directed graph contains a cycle.",
    "Return the shortest transformation sequence between two words.",
    "Count connected components in an undirected graph.",
  ],
  dp: [
    "Find the number of ways to climb n stairs with one or two steps.",
    "Return the maximum profit from non-adjacent house values.",
    "Compute the edit distance between two strings.",
  ],
};

const drillMeta = {
  arrays: "Pattern: two pointers or sliding window | Target: O(n) to O(n log n)",
  hashing: "Pattern: frequency map or prefix state | Target: O(n) average time",
  trees: "Pattern: DFS recursion and invariants | Target: O(n) time",
  graphs: "Pattern: BFS/DFS with visited state | Target: O(V + E) time",
  dp: "Pattern: define state and transition | Target: polynomial states",
};

function renderDemo(key) {
  const demo = demos[key];
  const max = Math.max(...demo.values);

  demoTitle.textContent = demo.title;
  demoDescription.textContent = demo.description;
  demoTime.textContent = demo.time;
  demoSpace.textContent = demo.space;
  bars.innerHTML = "";

  demo.values.forEach((value, index) => {
    const bar = document.createElement("span");
    bar.className = "bar";
    bar.style.height = `${Math.max(42, (value / max) * 210)}px`;
    bar.textContent = value;

    if (demo.highlights.includes(index)) {
      bar.classList.add("highlight");
    }

    if (demo.muted.includes(index)) {
      bar.classList.add("muted");
    }

    bars.appendChild(bar);
  });
}

function generateDrill(topic) {
  const prompts = drills[topic];
  const prompt = prompts[Math.floor(Math.random() * prompts.length)];

  challenge.innerHTML = `
    <strong>Prompt:</strong> ${prompt}
    <span>${drillMeta[topic]}</span>
  `;
}

navToggle.addEventListener("click", () => {
  const isOpen = navShell.classList.toggle("open");
  navToggle.setAttribute("aria-expanded", String(isOpen));
});

document.querySelectorAll(".nav-links a").forEach((link) => {
  link.addEventListener("click", () => {
    navShell.classList.remove("open");
    navToggle.setAttribute("aria-expanded", "false");
  });
});

tabs.forEach((tab) => {
  tab.addEventListener("click", () => {
    tabs.forEach((item) => {
      item.classList.remove("active");
      item.setAttribute("aria-selected", "false");
    });

    tab.classList.add("active");
    tab.setAttribute("aria-selected", "true");
    renderDemo(tab.dataset.demo);
  });
});

practiceForm.addEventListener("submit", (event) => {
  event.preventDefault();
  generateDrill(topicSelect.value);
});

renderDemo("binary");
