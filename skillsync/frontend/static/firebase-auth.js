/**
 * Keeps the existing Flask session flow while creating/signing-in Firebase
 * accounts in the browser. Passwords are sent only to Firebase Auth and are
 * never written to Firestore.
 */
import {
  createUserWithEmailAndPassword,
  signInWithEmailAndPassword,
  signOut,
  updateProfile,
} from "https://www.gstatic.com/firebasejs/10.14.1/firebase-auth.js";
import {
  doc,
  serverTimestamp,
  setDoc,
} from "https://www.gstatic.com/firebasejs/10.14.1/firebase-firestore.js";

function showFirebaseStatus(form, message) {
  let status = form.querySelector("[data-firebase-status]");
  if (!status) {
    status = document.createElement("p");
    status.dataset.firebaseStatus = "";
    status.className = "field-hint";
    status.setAttribute("role", "status");
    form.prepend(status);
  }
  status.textContent = message;
}

async function saveFirebaseProfile(firebase, user, { username, fullName }) {
  await setDoc(doc(firebase.db, "users", user.uid), {
    email: user.email,
    username,
    fullName: fullName || null,
    authProvider: "password",
    updatedAt: serverTimestamp(),
    createdAt: serverTimestamp(),
  }, { merge: true });
}

async function configureFirebaseAuth() {
  const firebase = await window.skillSyncFirebaseReady;
  const signupForm = document.querySelector("[data-firebase-signup]");
  const loginForm = document.querySelector("[data-firebase-login]");
  const logoutLink = document.querySelector("[data-firebase-logout]");

  if (signupForm) {
    signupForm.addEventListener("submit", async (event) => {
      if (signupForm.dataset.firebaseSubmitting === "true") return;
      event.preventDefault();

      const email = signupForm.elements.email.value.trim();
      const password = signupForm.elements.password.value;
      const username = signupForm.elements.username.value.trim();
      const fullName = signupForm.elements.full_name.value.trim();
      const submitButton = signupForm.querySelector("button[type='submit']");
      submitButton.disabled = true;

      try {
        const credential = await createUserWithEmailAndPassword(firebase.auth, email, password);
        if (fullName) await updateProfile(credential.user, { displayName: fullName });

        try {
          await saveFirebaseProfile(firebase, credential.user, { username, fullName });
        } catch (error) {
          console.warn("Firebase profile was not saved to Firestore.", error);
          showFirebaseStatus(signupForm, "Firebase account created. Firestore profile sync is pending.");
        }
      } catch (error) {
        // Flask signup still works when Firebase is unavailable. A duplicate
        // Firebase email is also safe because Flask validates duplicates.
        console.warn("Firebase signup was skipped.", error);
        showFirebaseStatus(signupForm, "Firebase signup is not available yet; creating the SkillSync account normally.");
      } finally {
        signupForm.dataset.firebaseSubmitting = "true";
        submitButton.disabled = false;
        signupForm.submit();
      }
    });
  }

  if (loginForm) {
    loginForm.addEventListener("submit", async (event) => {
      if (loginForm.dataset.firebaseSubmitting === "true") return;
      event.preventDefault();

      const identifier = loginForm.elements.identifier.value.trim();
      const password = loginForm.elements.password.value;
      // Firebase password sign-in uses email; local Flask still allows
      // username-based login.
      if (identifier.includes("@")) {
        try {
          await signInWithEmailAndPassword(firebase.auth, identifier, password);
        } catch (error) {
          console.warn("Firebase sign-in was skipped.", error);
        }
      }
      loginForm.dataset.firebaseSubmitting = "true";
      loginForm.submit();
    });
  }

  if (logoutLink) {
    logoutLink.addEventListener("click", () => {
      // Do not delay Flask logout if the Firebase request is offline.
      signOut(firebase.auth).catch((error) => console.warn("Firebase sign-out failed.", error));
    });
  }
}

configureFirebaseAuth().catch((error) => {
  console.warn("Firebase Auth could not be initialized.", error);
});
