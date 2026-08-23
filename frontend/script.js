// ============================================================================
// RAG CHATBOT FRONTEND
// Vanilla JavaScript
// FastAPI Backend
// ============================================================================


// ============================================================================
// CONFIG
// ============================================================================

const API_BASE = "http://127.0.0.1:8000";


// ============================================================================
// APPLICATION STATE
// ============================================================================

const state = {
  token: localStorage.getItem("rag_token") || null,
  sessionId: null,
  documents: []
};


// ============================================================================
// DOM ELEMENTS
// ============================================================================

const authScreen =
  document.getElementById("auth-screen");

const chatScreen =
  document.getElementById("chat-screen");

const loginForm =
  document.getElementById("login-form");

const registerForm =
  document.getElementById("register-form");

const authError =
  document.getElementById("auth-error");

const fileInput =
  document.getElementById("file-input");

const uploadStatus =
  document.getElementById("upload-status");

const docList =
  document.getElementById("doc-list");

const chatForm =
  document.getElementById("chat-form");

const chatInput =
  document.getElementById("chat-input");

const messagesEl =
  document.getElementById("messages");

const newChatBtn =
  document.getElementById("new-chat-btn");

const logoutBtn =
  document.getElementById("logout-btn");


// ============================================================================
// INIT
// ============================================================================

function init() {

  wireTabs();

  wireAuthForms();

  wireChat();

  wireUpload();

  updateDocumentCount();


  // New chat
  if (newChatBtn) {

    newChatBtn.addEventListener(
      "click",
      startNewChat
    );

  }


  // Logout
  if (logoutBtn) {

    logoutBtn.addEventListener(
      "click",
      logout
    );

  }


  // Check existing login
  if (state.token) {

    showChatScreen();

  } else {

    showAuthScreen();

  }

}


// ============================================================================
// SCREEN SWITCHING
// ============================================================================

function showAuthScreen() {

  if (authScreen) {

    authScreen.classList.add("active");

  }

  if (chatScreen) {

    chatScreen.classList.remove("active");

  }

}


function showChatScreen() {

  if (authScreen) {

    authScreen.classList.remove("active");

  }

  if (chatScreen) {

    chatScreen.classList.add("active");

  }


  // Start a new chat only if there are no messages
  if (
    messagesEl &&
    messagesEl.children.length === 0
  ) {

    startNewChat();

  }


  // Load documents
  loadDocuments();

}


// ============================================================================
// AUTH TABS
// ============================================================================

function wireTabs() {

  const tabButtons =
    document.querySelectorAll(".tab-btn");

  const authForms =
    document.querySelectorAll(".auth-form");


  tabButtons.forEach((btn) => {

    btn.addEventListener(
      "click",
      () => {

        // Remove active from all tabs
        tabButtons.forEach(
          (button) => {

            button.classList.remove(
              "active"
            );

          }
        );


        // Remove active from all forms
        authForms.forEach(
          (form) => {

            form.classList.remove(
              "active"
            );

          }
        );


        // Activate clicked tab
        btn.classList.add("active");


        const tabName =
          btn.dataset.tab;


        const targetForm =
          document.getElementById(
            `${tabName}-form`
          );


        if (targetForm) {

          targetForm.classList.add(
            "active"
          );

        }


        if (authError) {

          authError.textContent = "";

          authError.style.color = "";

        }

      }
    );

  });

}


// ============================================================================
// AUTH FORMS
// ============================================================================

function wireAuthForms() {


  // ==========================================================================
  // LOGIN
  // ==========================================================================

  if (loginForm) {

    loginForm.addEventListener(
      "submit",
      async (e) => {

        e.preventDefault();


        if (authError) {

          authError.textContent = "";

          authError.style.color = "";

        }


        const email =
          document
            .getElementById("login-email")
            .value
            .trim();


        const password =
          document
            .getElementById("login-password")
            .value;


        if (!email || !password) {

          authError.textContent =
            "Email and password are required.";

          return;

        }


        try {

          console.log(
            "Sending login request..."
          );


          // FastAPI OAuth2PasswordRequestForm
          // expects username + password
          const formData =
            new URLSearchParams();


          formData.append(
            "username",
            email
          );


          formData.append(
            "password",
            password
          );


          const response =
            await fetch(
              `${API_BASE}/auth/login`,
              {
                method: "POST",

                headers: {

                  "Content-Type":
                    "application/x-www-form-urlencoded",

                  "Accept":
                    "application/json"

                },

                body:
                  formData.toString()

              }
            );


          console.log(
            "Login status:",
            response.status
          );


          let data = {};

          try {

            data =
              await response.json();

          } catch (jsonError) {

            console.error(
              "Invalid JSON response:",
              jsonError
            );

          }


          console.log(
            "Login response:",
            data
          );


          if (!response.ok) {

            if (
              response.status === 422
            ) {

              authError.textContent =
                "Invalid login data. Please check email and password.";

            }

            else if (
              response.status === 401
            ) {

              authError.textContent =
                "Invalid email or password.";

            }

            else {

              authError.textContent =
                data.detail ||
                "Login failed.";

            }


            return;

          }


          if (!data.access_token) {

            console.error(
              "Access token missing:",
              data
            );


            authError.textContent =
              "Login successful, but access token was not received.";

            return;

          }


          // Save token
          state.token =
            data.access_token;


          localStorage.setItem(
            "rag_token",
            data.access_token
          );


          localStorage.setItem(
            "rag_token_type",
            data.token_type || "bearer"
          );


          console.log(
            "Login successful!"
          );


          loginForm.reset();


          showChatScreen();

        }


        catch (error) {

          console.error(
            "Login error:",
            error
          );


          authError.textContent =
            "Cannot connect to backend. Make sure FastAPI is running.";

        }

      }
    );

  }


  // ==========================================================================
  // REGISTER
  // ==========================================================================

  if (registerForm) {

    registerForm.addEventListener(
      "submit",
      async (e) => {

        e.preventDefault();


        authError.textContent = "";

        authError.style.color = "";


        const full_name =
          document
            .getElementById("register-name")
            .value
            .trim();


        const email =
          document
            .getElementById("register-email")
            .value
            .trim();


        const password =
          document
            .getElementById("register-password")
            .value;


        if (!email || !password) {

          authError.textContent =
            "Email and password are required.";

          return;

        }


        try {

          console.log(
            "Sending registration request..."
          );


          const response =
            await fetch(
              `${API_BASE}/auth/register`,
              {

                method: "POST",

                headers: {

                  "Content-Type":
                    "application/json",

                  "Accept":
                    "application/json"

                },

                body:
                  JSON.stringify({

                    full_name:
                      full_name,

                    email:
                      email,

                    password:
                      password

                  })

              }
            );


          let data = {};


          try {

            data =
              await response.json();

          }

          catch (error) {

            console.error(
              "Invalid registration response:",
              error
            );

          }


          console.log(
            "Register status:",
            response.status
          );


          console.log(
            "Register response:",
            data
          );


          if (!response.ok) {

            authError.style.color = "";

            authError.textContent =
              data.detail ||
              "Registration failed.";

            return;

          }


          authError.style.color =
            "#6cff9a";


          authError.textContent =
            "Account created successfully! Please login.";


          registerForm.reset();


          const loginTab =
            document.querySelector(
              '.tab-btn[data-tab="login"]'
            );


          if (loginTab) {

            loginTab.click();

          }

        }


        catch (error) {

          console.error(
            "Registration error:",
            error
          );


          authError.style.color = "";

          authError.textContent =
            "Cannot connect to backend.";

        }

      }
    );

  }

}


// ============================================================================
// LOGOUT
// ============================================================================

function logout() {

  state.token = null;

  state.sessionId = null;

  state.documents = [];


  localStorage.removeItem(
    "rag_token"
  );


  localStorage.removeItem(
    "rag_token_type"
  );


  if (docList) {

    docList.innerHTML = "";

  }


  if (messagesEl) {

    messagesEl.innerHTML = "";

  }


  if (uploadStatus) {

    uploadStatus.textContent = "";

  }


  updateDocumentCount();


  showAuthScreen();

}


// ============================================================================
// UPLOAD
// ============================================================================

function wireUpload() {

  if (!fileInput) {

    return;

  }


  fileInput.addEventListener(
    "change",
    async () => {

      const file =
        fileInput.files[0];


      if (!file) {

        return;

      }


      if (!state.token) {

        uploadStatus.textContent =
          "Please login first.";

        return;

      }


      const fileName =
        file.name.toLowerCase();


      const allowedExtensions = [
        ".pdf",
        ".txt",
        ".md"
      ];


      const valid =
        allowedExtensions.some(
          (extension) =>
            fileName.endsWith(extension)
        );


      if (!valid) {

        uploadStatus.textContent =
          "Only PDF, TXT and MD files are allowed.";

        fileInput.value = "";

        return;

      }


      uploadStatus.textContent =
        `Indexing "${file.name}"...`;


      const formData =
        new FormData();


      formData.append(
        "file",
        file
      );


      try {

        const response =
          await fetch(
            `${API_BASE}/upload`,
            {

              method: "POST",

              headers: {

                Authorization:
                  `Bearer ${state.token}`

              },

              body:
                formData

            }
          );


        let data = {};


        try {

          data =
            await response.json();

        }

        catch (error) {

          console.error(
            "Invalid upload response:",
            error
          );

        }


        console.log(
          "Upload status:",
          response.status
        );


        console.log(
          "Upload response:",
          data
        );


        if (!response.ok) {

          if (
            response.status === 401
          ) {

            uploadStatus.textContent =
              "Session expired. Please login again.";

            logout();

            return;

          }


          if (
            response.status === 409
          ) {

            uploadStatus.textContent =
              "This document already exists.";

            return;

          }


          uploadStatus.textContent =
            `Error: ${
              data.detail ||
              "Upload failed"
            }`;

          return;

        }


        const documentName =
          data.document_name ||
          file.name;


        const chunksIndexed =
          data.chunks_indexed ||
          data.chunk_count ||
          0;


        const documentId =
          data.document_id ||
          data.id ||
          null;


        uploadStatus.textContent =
          `Indexed ${chunksIndexed} chunks.`;


        // Reload from backend so the sidebar
        // and count always use the database state.
        await loadDocuments();


        console.log(
          "Uploaded document:",
          documentName,
          documentId
        );

      }


      catch (error) {

        console.error(
          "Upload error:",
          error
        );


        uploadStatus.textContent =
          `Error: ${error.message}`;

      }


      finally {

        fileInput.value = "";

      }

    }
  );

}


// ============================================================================
// DOCUMENT COUNT
// ============================================================================

function updateDocumentCount() {

  let countEl =
    document.getElementById(
      "document-count"
    );


  // If #document-count does not exist,
  // create it automatically.
  if (!countEl) {

    const documentsHeader =
      document.querySelector(
        ".documents-header"
      );


    if (documentsHeader) {

      countEl =
        document.createElement(
          "span"
        );

      countEl.id =
        "document-count";


      documentsHeader.appendChild(
        countEl
      );

    }

    else {

      // Fallback for old HTML where
      // "Your documents 0" is inside h2.
      const headings =
        document.querySelectorAll(
          "h2, h3"
        );


      for (
        const heading of headings
      ) {

        const text =
          heading.textContent
            .trim()
            .toLowerCase();


        if (
          text.startsWith(
            "your documents"
          )
        ) {

          countEl =
            document.createElement(
              "span"
            );

          countEl.id =
            "document-count";


          heading.textContent =
            "Your documents";


          heading.appendChild(
            countEl
          );


          break;

        }

      }

    }

  }


  if (countEl) {

    countEl.textContent =
      state.documents.length;

  }

}


// ============================================================================
// ADD DOCUMENT TO SIDEBAR
// ============================================================================

function addDocToList(
  name,
  chunkCount,
  documentId = null
) {

  if (!name) {

    return;

  }


  // Prevent duplicate UI documents
  const existing =
    state.documents.find(
      (doc) =>
        doc.name === name
    );


  if (existing) {

    if (
      documentId &&
      !existing.id
    ) {

      existing.id =
        documentId;

    }


    updateDocumentCount();

    return;

  }


  const doc = {

    id:
      documentId,

    name:
      name,

    chunkCount:
      chunkCount,

    selected:
      true

  };


  state.documents.push(
    doc
  );


  const li =
    document.createElement(
      "li"
    );


  li.className =
    "document-item";


  // Checkbox
  const checkbox =
    document.createElement(
      "input"
    );


  checkbox.type =
    "checkbox";


  checkbox.checked =
    true;


  checkbox.className =
    "doc-checkbox";


  checkbox.title =
    "Include this document in search";


  checkbox.addEventListener(
    "change",
    () => {

      doc.selected =
        checkbox.checked;

    }
  );


  // Document name
  const label =
    document.createElement(
      "span"
    );


  label.className =
    "doc-name";


  label.textContent =
    `${name} (${chunkCount} chunks)`;


  label.title =
    name;


  // Delete button
  const deleteBtn =
    document.createElement(
      "button"
    );


  deleteBtn.type =
    "button";


  deleteBtn.className =
    "delete-doc-btn";


  deleteBtn.textContent =
    "🗑";


  deleteBtn.title =
    "Delete document";


  deleteBtn.addEventListener(
    "click",
    () => {

      deleteDocument(
        doc,
        li
      );

    }
  );


  // Build
  li.appendChild(
    checkbox
  );


  li.appendChild(
    label
  );


  li.appendChild(
    deleteBtn
  );


  // Add to sidebar
  docList.prepend(
    li
  );


  updateDocumentCount();

}


// ============================================================================
// DELETE DOCUMENT
// ============================================================================

async function deleteDocument(
  doc,
  listItem
) {

  if (!doc.id) {

    alert(
      "Document ID is not available. Please refresh the page and try again."
    );

    return;

  }


  const confirmed =
    confirm(
      `Are you sure you want to delete "${doc.name}"?`
    );


  if (!confirmed) {

    return;

  }


  try {

    uploadStatus.textContent =
      `Deleting "${doc.name}"...`;


    const response =
      await fetch(
        `${API_BASE}/documents/${doc.id}`,
        {

          method: "DELETE",

          headers: {

            Authorization:
              `Bearer ${state.token}`,

            Accept:
              "application/json"

          }

        }
      );


    let data = {};


    try {

      data =
        await response.json();

    }

    catch (error) {

      console.log(
        "Delete response has no JSON body."
      );

    }


    console.log(
      "Delete status:",
      response.status
    );


    console.log(
      "Delete response:",
      data
    );


    if (!response.ok) {

      if (
        response.status === 401
      ) {

        alert(
          "Session expired. Please login again."
        );

        logout();

        return;

      }


      throw new Error(
        data.detail ||
        `Failed to delete document (${response.status})`
      );

    }


    // Remove from state
    state.documents =
      state.documents.filter(
        (item) =>
          item.id !== doc.id
      );


    // Remove from UI
    if (listItem) {

      listItem.remove();

    }


    updateDocumentCount();


    // Reset chat session
    state.sessionId =
      null;


    uploadStatus.textContent =
      `Deleted "${doc.name}".`;

  }


  catch (error) {

    console.error(
      "Delete error:",
      error
    );


    alert(
      `Error: ${error.message}`
    );


    uploadStatus.textContent =
      "Delete failed.";

  }

}


// ============================================================================
// CHAT
// ============================================================================

function wireChat() {

  if (!chatForm) {

    return;

  }


  chatForm.addEventListener(
    "submit",
    async (e) => {

      e.preventDefault();


      const question =
        chatInput.value.trim();


      if (!question) {

        return;

      }


      if (!state.token) {

        appendMessage(
          "assistant",
          "Please login first."
        );

        return;

      }


      // User message
      appendMessage(
        "user",
        question
      );


      chatInput.value =
        "";


      // Loading
      const loadingEl =
        appendMessage(
          "assistant",
          "Thinking...",
          {
            loading: true
          }
        );


      // Selected documents
      const selectedDocuments =
        state.documents
          .filter(
            (doc) =>
              doc.selected
          )
          .map(
            (doc) =>
              doc.name
          );


      // Require document
      if (
        selectedDocuments.length === 0
      ) {

        loadingEl.remove();


        appendMessage(
          "assistant",
          "Please select at least one document before asking a question."
        );


        return;

      }


      try {

        console.log(
          "Sending chat request..."
        );


        const response =
          await fetch(
            `${API_BASE}/chat`,
            {

              method: "POST",

              headers: {

                "Content-Type":
                  "application/json",

                "Accept":
                  "application/json",

                Authorization:
                  `Bearer ${state.token}`

              },

              body:
                JSON.stringify({

                  message:
                    question,

                  session_id:
                    state.sessionId,

                  selected_documents:
                    selectedDocuments

                })

            }
          );


        let data = {};


        try {

          data =
            await response.json();

        }

        catch (error) {

          console.error(
            "Invalid chat response:",
            error
          );

        }


        console.log(
          "Chat status:",
          response.status
        );


        console.log(
          "Chat response:",
          data
        );


        if (!response.ok) {

          if (
            response.status === 401
          ) {

            loadingEl.remove();


            appendMessage(
              "assistant",
              "Your session has expired. Please login again."
            );


            logout();

            return;

          }


          throw new Error(
            data.detail ||
            `Chat request failed (${response.status})`
          );

        }


        // Session
        state.sessionId =
          data.session_id ||
          state.sessionId;


        // Remove loading
        loadingEl.remove();


        // Assistant answer
        appendMessage(
          "assistant",
          data.answer ||
          "No answer received.",
          {

            sources:
              data.sources || []

          }
        );

      }


      catch (error) {

        console.error(
          "Chat error:",
          error
        );


        loadingEl.remove();


        appendMessage(
          "assistant",
          `⚠️ ${error.message}`
        );

      }

    }
  );

}


// ============================================================================
// APPEND MESSAGE
// ============================================================================

function appendMessage(
  role,
  text,
  opts = {}
) {

  const el =
    document.createElement(
      "div"
    );


  el.className =
    `msg ${role}${
      opts.loading
        ? " loading"
        : ""
    }`;


  // Main message
  el.textContent =
    text;


  // Sources
  if (
    opts.sources &&
    opts.sources.length
  ) {

    const sourcesEl =
      document.createElement(
        "div"
      );


    sourcesEl.className =
      "sources";


    const strong =
      document.createElement(
        "strong"
      );


    strong.textContent =
      "Sources";


    sourcesEl.appendChild(
      strong
    );


    opts.sources.forEach(
      (source) => {

        const sourceItem =
          document.createElement(
            "div"
          );


        sourceItem.className =
          "source-item";


        const documentName =
          source.document_name ||
          source.document ||
          "Unknown document";


        const page =
          source.page_number;


        const chunk =
          source.chunk_index;


        const score =
          source.score;


        sourceItem.textContent =
          `📄 ${documentName}` +

          (
            page !== undefined &&
            page !== null
              ? ` · Page ${page}`
              : ""
          ) +

          (
            chunk !== undefined &&
            chunk !== null
              ? ` · Chunk ${chunk}`
              : ""
          ) +

          (
            score !== undefined &&
            score !== null
              ? ` · Score ${Number(score).toFixed(4)}`
              : ""
          );


        sourcesEl.appendChild(
          sourceItem
        );

      }
    );


    el.appendChild(
      sourcesEl
    );

  }


  messagesEl.appendChild(
    el
  );


  messagesEl.scrollTop =
    messagesEl.scrollHeight;


  return el;

}


// ============================================================================
// LOAD DOCUMENTS
// ============================================================================

async function loadDocuments() {

  if (!state.token) {

    return;

  }


  try {

    console.log(
      "Loading documents..."
    );


    const response =
      await fetch(
        `${API_BASE}/documents`,
        {

          method: "GET",

          headers: {

            Authorization:
              `Bearer ${state.token}`,

            Accept:
              "application/json"

          }

        }
      );


    console.log(
      "Documents status:",
      response.status
    );


    // Unauthorized
    if (
      response.status === 401
    ) {

      console.log(
        "Token expired."
      );


      logout();

      return;

    }


    // Backend endpoint missing
    if (
      response.status === 404
    ) {

      console.warn(
        "GET /documents endpoint not found in backend."
      );


      state.documents =
        [];


      updateDocumentCount();

      return;

    }


    let data = [];


    try {

      data =
        await response.json();

    }

    catch (error) {

      console.error(
        "Invalid documents response:",
        error
      );


      return;

    }


    if (!response.ok) {

      throw new Error(
        data.detail ||
        "Failed to load documents"
      );

    }


    // Reset state
    state.documents =
      [];


    if (docList) {

      docList.innerHTML =
        "";

    }


    // Add documents
    if (
      Array.isArray(data)
    ) {

      data.forEach(
        (doc) => {

          addDocToList(

            doc.filename ||
            doc.document_name ||
            doc.name,

            doc.chunk_count ||
            doc.chunks_indexed ||
            0,

            doc.id ||
            doc.document_id ||
            null

          );

        }
      );

    }


    // IMPORTANT:
    // Update the actual document count.
    updateDocumentCount();


    console.log(
      "Documents loaded:",
      state.documents
    );

  }


  catch (error) {

    console.error(
      "Failed to load documents:",
      error
    );

  }

}


// ============================================================================
// NEW CHAT
// ============================================================================

function startNewChat() {

  state.sessionId =
    null;


  if (messagesEl) {

    messagesEl.innerHTML =
      "";

  }


  appendMessage(
    "assistant",
    "Hi! Upload a document and ask me anything about it."
  );

}


// ============================================================================
// SUGGESTION BUTTONS
// ============================================================================

function wireSuggestions() {

  const suggestions =
    document.querySelectorAll(
      ".suggestion"
    );


  suggestions.forEach(
    (button) => {

      button.addEventListener(
        "click",
        () => {

          if (!chatInput) {

            return;

          }


          chatInput.value =
            button.textContent.trim();


          chatInput.focus();

        }
      );

    }
  );

}


// ============================================================================
// START APPLICATION
// ============================================================================

document.addEventListener(
  "DOMContentLoaded",
  () => {

    init();

    wireSuggestions();

  }
);