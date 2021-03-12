import rockset from "rockset"
import nodemailer from "nodemailer"
import fs from "fs"

if (process.argv[2] == null) {
    throw new Error("No email file specified")
}
if (process.argv[3] == null) {
    throw new Error("No subject specified")
}

const rocksetClient = rockset.default(process.env.RS2_TOKEN)

function send_mail(recievers, file, subject) {

    fs.readFile(file, "utf8", (err, message) => {
        if (err) {
            console.error(err)
        }
        else {
            nodemailer.createTransport({
                service: "gmail",
                auth: {
                    user: process.env.EMAIL_EMAIL,
                    pass: process.env.EMAIL_PW
                }
            }).sendMail({
                from: process.env.EMAIL_EMAIL,
                to: recievers,
                subject: subject,
                html: message
            }, function(error){
                if (error) {
                    console.log(error);
                } else {
                    console.log("Email sent.");
                }
            })  
        }
    })
}

rocksetClient.queries
    .query({
        sql: {
            query: "SELECT _id FROM harker_hackers.emails",
        }
    }).then(
        function(data){
            var res = data.results
            var email_file = process.argv[2]

            var email_addresses = []
            for (var key in res) {
                email_addresses.push(res[key]._id)
            }
            send_mail(email_addresses, process.argv[2], process.argv[3])
        })
            .catch(console.error)