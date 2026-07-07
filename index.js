const express = require("express");
const cors = require("cors");

const app = express();

app.use(cors());
app.use(express.json());

const API_KEY = "ak_vjdlxj26b3f4h9qt53y4nzts";

app.post("/analytics", (req, res) => {

    const key = req.header("X-API-Key");

    if (key !== API_KEY) {
        return res.status(401).json({
            error: "Unauthorized"
        });
    }

    const events = req.body.events || [];

    const total_events = events.length;

    const users = new Set();

    let revenue = 0;

    const totals = {};

    for (const event of events) {

        users.add(event.user);

        if (event.amount > 0) {

            revenue += event.amount;

            totals[event.user] =
                (totals[event.user] || 0) + event.amount;
        }
    }

    let top_user = "";

    let best = -1;

    for (const user in totals) {

        if (totals[user] > best) {

            best = totals[user];

            top_user = user;
        }
    }

    res.json({

        email: "24f2003563@ds.study.iitm.ac.in",

        total_events,

        unique_users: users.size,

        revenue,

        top_user
    });

});

const PORT = process.env.PORT || 3000;

app.listen(PORT, () => {

    console.log("Server running");
});