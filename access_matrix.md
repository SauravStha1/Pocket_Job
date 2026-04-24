
## **Access Matrix**

An Access Matrix is a table used in system security to define which **roles (users)** have access to specific **system operations**.

### **Legend**

* **C** = Create
* **R** = Read (view/list)
* **U** = Update
* **D** = Delete
* **✓** = Access allowed

---

### **Roles**

* **AD** = Admin
* **RC** = Recruiter
* **AP** = Applicant

---

## **Access Matrix Table**

| Module    | Action             | Type | AD | RC | AP |
| --------- | ------------------ | ---- | -- | -- | -- |
| **Users** | Manage users       | C    | ✓  |    |    |
| Users     | Manage users       | R    | ✓  |    |    |
| Users     | Manage users       | U    | ✓  |    |    |
| Users     | Manage users       | D    | ✓  |    |    |
| Users     | View own profile   | R    | ✓  | ✓  | ✓  |
| Users     | Update own profile | U    | ✓  | ✓  | ✓  |
| Users     | Change password    | U    | ✓  | ✓  | ✓  |

---

| Module   | Action     | Type | AD | RC | AP |
| -------- | ---------- | ---- | -- | -- | -- |
| **Jobs** | Post job   | C    | ✓  | ✓  |    |
| Jobs     | View jobs  | R    | ✓  | ✓  | ✓  |
| Jobs     | Update job | U    | ✓  | ✓  |    |
| Jobs     | Delete job | D    | ✓  | ✓  |    |

---

| Module           | Action                    | Type | AD | RC | AP |
| ---------------- | ------------------------- | ---- | -- | -- | -- |
| **Applications** | Apply for job             | C    |    |    | ✓  |
| Applications     | View applications         | R    | ✓  | ✓  | ✓  |
| Applications     | Update application status | U    | ✓  | ✓  |    |
| Applications     | Delete application        | D    | ✓  |    | ✓  |

---

| Module         | Action    | Type | AD | RC | AP |
| -------------- | --------- | ---- | -- | -- | -- |
| **CV/Profile** | Upload CV | C    |    |    | ✓  |
| CV/Profile     | View CV   | R    | ✓  | ✓  | ✓  |
| CV/Profile     | Update CV | U    |    |    | ✓  |
| CV/Profile     | Delete CV | D    | ✓  |    | ✓  |

---

| Module          | Action                | Type | AD | RC | AP |
| --------------- | --------------------- | ---- | -- | -- | -- |
| **Chat System** | Start chat            | C    |    | ✓  |    |
| Chat System     | Send/Receive messages | R    |    | ✓  | ✓  |

---

| Module       | Action                     | Type | AD | RC | AP |
| ------------ | -------------------------- | ---- | -- | -- | -- |
| **Payments** | Make payment (job posting) | C    |    | ✓  |    |
| Payments     | View payment history       | R    | ✓  | ✓  |    |

---

| Module          | Action            | Type  | AD | RC | AP |
| --------------- | ----------------- | ----- | -- | -- | -- |
| **Admin Panel** | Monitor jobs      | R     | ✓  |    |    |
| Admin Panel     | Manage categories | C/U/D | ✓  |    |    |
| Admin Panel     | View reports      | R     | ✓  |    |    |

---
