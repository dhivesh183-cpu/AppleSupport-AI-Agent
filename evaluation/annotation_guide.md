# Golden Set Annotation Guide

## Purpose

This guide is used to manually label customer-support messages for the
AppleSupport AI customer-support agent.

## Allowed intents

1. `ios_or_software_update` — iOS, software, or update problems
2. `device_or_hardware` — physical device or hardware problems
3. `battery_or_charging` — battery, charging, or charger problems
4. `account_or_icloud` — Apple ID, iCloud, password, or verification problems
5. `purchase_or_billing` — purchases, payments, charges, refunds, or billing
6. `connectivity_or_network` — Wi-Fi, Bluetooth, internet, or connection problems
7. `app_or_media_service` — apps, iTunes, Apple Music, or media services
8. `order_or_repair` — repairs, replacement, orders, delivery, or service
9. `support_contact_or_dm` — contacting Apple Support, DM, calls, or support requests
10. `general_or_other` — unclear or none of the above

## Annotation procedure

Read the customer message and select the single intent that best describes
the customer's main issue.

Do not use model predictions when assigning the human label.

For ambiguous messages, choose the category that best represents the main
problem expressed by the customer.

## Important sampling note

The 200-example golden set contains 20 examples per intent. It was created
for balanced evaluation coverage and is therefore not representative of the
natural frequency of intents in the complete dataset.

## Human agreement

A second annotator independently labelled 40 examples. Agreement was measured
using raw agreement and Cohen's kappa.
