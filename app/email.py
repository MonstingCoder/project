from dotenv import load_dotenv
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from pydantic import EmailStr
from os import getenv
from uuid import UUID
# import socket


# socket.setdefaulttimeout(50)
load_dotenv(r'app/secret/.env')
conf = ConnectionConfig(
    MAIL_USERNAME=getenv("MAIL_USERNAME"),
    MAIL_PASSWORD=getenv("MAIL_PASSWORD"),
    MAIL_FROM=getenv("MAIL_USERNAME"),
    MAIL_FROM_NAME="Jaws Custom's Crew",
    MAIL_SERVER="smtp.gmail.com",
    MAIL_PORT=587,
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
)


def get_payment_email(data: dict, upload_link: str, referral_code: UUID):
    account_number = getenv("BANK_ACCOUNT_NUMBER")

    item_rows = []
    for item in data["items"]:
        subtotal = item["price"] * item["quantity"]
        item_rows.append(f"""
        <tr>
          <td style="padding:6px 0;">{item['name']}</td>
          <td align="center">{item['quantity']}</td>
          <td align="right">Rp{subtotal:,}</td>
        </tr>
        """)

    html = f"""
<!DOCTYPE html>
<html>
  <body style="margin:0; padding:0; background:#f4f4f4; font-family:Arial, sans-serif;">
    <table width="100%" cellpadding="0" cellspacing="0">
      <tr>
        <td align="center" style="padding:20px;">
          <table width="600" style="background:#ffffff; border-radius:8px; padding:24px;">

            <tr>
              <td>
                <h2>Halo 👋</h2>
                <p>Terima kasih telah melakukan pemesanan di <b>Jaws Custom's Crew</b>.</p>
              </td>
            </tr>

            <tr><td><hr></td></tr>

            <tr>
              <td>
                <h3>🛒 Detail Belanja</h3>
                <table width="100%" style="border-collapse:collapse; font-size:14px;">
                  <tr style="background:#f0f0f0;">
                    <th align="left">Item</th>
                    <th>Qty</th>
                    <th align="right">Subtotal</th>
                  </tr>
                  {''.join(item_rows)}
                </table>
              </td>
            </tr>

            <tr>
              <td style="padding-top:16px;">
                <h3>💰 Total Pembayaran</h3>
                <div style="
                  background:#f8f8f8;
                  border:1px dashed #ccc;
                  padding:10px;
                  font-family:monospace;
                  font-size:16px;
                  display:inline-block;
                ">
                  Rp{data['total']:,}
                </div>
              </td>
            </tr>

            <tr>
              <td style="padding-top:12px;">
                <h3>🏦 Informasi Pembayaran</h3>

                <p>Nomor Rekening:</p>
                <div style="
                  background:#f8f8f8;
                  border:1px dashed #ccc;
                  padding:8px;
                  font-family:monospace;
                ">
                  {account_number}
                </div>

                <p style="margin-top:10px;">Kode Referral:</p>
                <div style="
                  background:#f8f8f8;
                  border:1px dashed #ccc;
                  padding:8px;
                  font-family:monospace;
                ">
                  {referral_code}
                </div>
              </td>
            </tr>

            <!-- LINK (bukan tombol) -->
            <tr>
              <td style="padding-top:20px;">
                <p style="margin-bottom:6px;">
                  📎 <b>Upload bukti pembayaran melalui link berikut:</b>
                </p>
                <p style="margin:0;">
                  <a href="{upload_link}"
                     style="
                       color:#0066cc;
                       text-decoration:underline;
                       word-break:break-all;
                     ">
                    {upload_link}
                  </a>
                </p>
              </td>
            </tr>

            <tr>
              <td style="font-size:12px; color:#666; padding-top:16px;">
                <p>
                  Silakan tap & tahan (mobile) atau klik & drag (desktop)
                  untuk menyalin nomor rekening dan kode referral.
                </p>
                <p>— Jaws Custom's Crew</p>
              </td>
            </tr>

          </table>
        </td>
      </tr>
    </table>
  </body>
</html>
"""

    return html


async def send_payment_email(
    to_email: EmailStr,
    data: dict,
    upload_link: str,
    referral_code: UUID
):
    body = get_payment_email(data, upload_link, referral_code)

    message = MessageSchema(
        subject="Instruksi Pembayaran Pesanan Anda",
        recipients=[to_email],
        body=body,
        subtype='html',
    )

    fm = FastMail(conf)
    await fm.send_message(message)
