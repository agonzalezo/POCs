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
    const queue = 'hello'
    const conn = await amqplib.connect(`amqp://${mquser}:${mqpass}@${mqhost}`)
    const ch1 = await conn.createChannel()
    await ch1.assertQueue(queue, { durable: true })

    ch1.consume(queue, (msg) => {
        if (msg !== null) {
            console.log('Recieved:', msg.content.toString())
            ch1.ack(msg)
        } else {
            console.log('Consumer cancelled by server')
        }
    }, { noAck: false })
} catch (error) {
    throw new Error(error)
}
