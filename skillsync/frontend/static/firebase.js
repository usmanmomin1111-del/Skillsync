/**
 * Shared Firebase client for SkillSync.
 *
 * The config is provided by Flask in base.html so it can be changed through
 * environment variables at deployment time. Firebase web config values identify
 * a project; they are not server credentials.
 */
import { initializeApp, getApps, getApp } from "https://www.gstatic.com/firebasejs/10.14.1/firebase-app.js";
import { getAuth } from "https://www.gstatic.com/firebasejs/10.14.1/firebase-auth.js";
import { getFirestore } from "https://www.gstatic.com/firebasejs/10.14.1/firebase-firestore.js";
import { getAnalytics, isSupported } from "https://www.gstatic.com/firebasejs/10.14.1/firebase-analytics.js";

// Flask renders this JSON in base.html. Keeping it in a JSON script tag means
// VS Code can validate the Jinja template without treating `{{ ... }}` as
// invalid JavaScript.
const configElement = document.getElementById("skillsync-firebase-config");
let config = null;
try {
  config = JSON.parse(configElement?.textContent || "null");
} catch (error) {
  console.warn("Firebase configuration could not be read.", error);
}
let resolveFirebaseReady;
let rejectFirebaseReady;

// Other browser modules wait on this promise before accessing Auth/Firestore.
// It avoids a race where firebase-auth.js runs before Firebase has finished
// loading from the CDN.
window.skillSyncFirebaseReady = new Promise((resolve, reject) => {
  resolveFirebaseReady = resolve;
  rejectFirebaseReady = reject;
});

if (!config || !config.apiKey || !config.projectId) {
  const error = new Error("Firebase was not initialized: missing web configuration.");
  console.warn(error.message);
  rejectFirebaseReady(error);
} else {
  try {
    const app = getApps().length ? getApp() : initializeApp(config);
    const auth = getAuth(app);
    const db = getFirestore(app);

    // Analytics is unsupported in some browsers (and in local/private contexts),
    // so it must not stop Auth or Firestore from becoming available.
    let analytics = null;
    try {
      if (await isSupported()) {
        analytics = getAnalytics(app);
      }
    } catch (error) {
      console.info("Firebase Analytics is unavailable in this browser.", error);
    }

    window.skillSyncFirebase = { app, auth, db, analytics };
    resolveFirebaseReady(window.skillSyncFirebase);
    window.dispatchEvent(new CustomEvent("skillsync:firebase-ready", {
      detail: window.skillSyncFirebase,
    }));
  } catch (error) {
    console.error("Firebase initialization failed.", error);
    rejectFirebaseReady(error);
  }
}
