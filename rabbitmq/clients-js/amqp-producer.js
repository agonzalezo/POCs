#!/usr/bin/env node
/* eslint-disable indent */
/* eslint-disable space-before-function-paren */
import amqplib from 'amqplib'
import dotenv from 'dotenv'
dotenv.config()
const mquser = process.env.MQUSER
const mqpass = process.env.MQPASS
const mqhost = process.env.MQHOST

try {
    // Sender
    const message = 'Hello World! '
    const queue = 'hello'
    const conn = await amqplib.connect(`amqp://${mquser}:${mqpass}@${mqhost}`)
    // const ch1 = await conn.createChannel()
    const ch2 = await conn.createConfirmChannel()
    await ch2.assertQueue(queue, { durable: true })
    await send(ch2, queue, message)
    console.log(' [x] Sent %s', message)
    ch2.close()
    conn.close()
    process.exit(0)
} catch (error) {
    throw new Error(error)
}

async function send(ch2, queue, message) {
    return new Promise(async (resolve, reject) => {
        for (let index = 1; index <= 20000; index++) {
            // ch2.sendToQueue(queue, message)
            ch2.sendToQueue(queue, Buffer.from(message + `${index}`), { persistent: true }, (err, ok) => {
                if (err) console.error(err)
            })
        }
        await ch2.waitForConfirms()
        resolve()
    }
    )
}
