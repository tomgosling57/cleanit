# Cleaner Management Web Application – Planning Document (Option A Focus)

## 1. Core Requirements

* **Database persistence**: Relational DB (Postgres/MySQL/SQLite dev) to store users, roles, teams, jobs, assignments.
* **Roles & Security Clearances**:

  * Cleaner: view own schedule only.
  * Team leader: view/modify their team’s timetable.
  * Owner: full access and management.
* **Timetable View**:

  * Daily schedule filtered by date.
  * Kanban-style view: columns for teams, jobs as cards.
  * Drag-and-drop to reassign jobs between teams.
* **UI/UX Goals**:

  * Focus on visual polish.
  * Responsive layout for desktop & mobile.
  * Use existing libraries where possible.

---

## 2. Frontend Approach – Option A: Flask + Jinja + htmx + dragulajs

### Why Flask + Jinjacode

* Familiar stack leveraging Flask and Jinja templates.
* Minimal learning curve and fast delivery.
* htmx enables AJAX-style updates without a full SPA.
* dragulajs provides polished drag-and-drop functionality.
* Persistence flows naturally: drag triggers POST to backend → updates database → server re-renders relevant column.

### Implementation Details

* **Templates**: Jinja templates render jobs as cards within team columns.
* **Drag-and-Drop**: dragulajs initialized on team columns.

  * `onEnd` event fires a POST via htmx to update job assignment in the database.
* **Backend Routes**:

  * `GET /timetable` – render daily timetable.
  * `POST /update-job` – receive job ID and new team ID, update DB.
* **Visuals**:

  * Use TailwindCSS for responsive, polished layout.
  * Optional animation effects for drag-and-drop for better UX.

### Persistence

* Dragged jobs persist immediately because the htmx POST updates the database.
* Any page reload will reflect the updated timetable.

---

## 3. Mobile Considerations

* Works well as a responsive mobile-friendly website.
* Future app conversion possible using **Capacitor/Cordova** to wrap the web app.
* Native features (push notifications, offline) would require additional work.

---

## 4. App Store Publishing (if wrapped in Capacitor)

### Apple App Store

* Developer account: \$99/year.
* Mac + Xcode required for build/signing.
* Upload and undergo Apple review (1–3 days). Ensure the app doesn’t feel like just a website.

### Google Play Store

* Developer account: \$25 one-time fee.
* Build APK/AAB, upload via Play Console.
* Automatic review (hours to a day).

### Common Requirements

* App icons & splash screens.
* Privacy policy & metadata.
* Versioning for updates.
* Optional beta testing before public release.

