import mysql.connector
from flask import Flask, render_template, request, session
from datetime import datetime, timedelta
from functools import wraps


app = Flask(__name__)
app.secret_key = "f5c18f9f5e97a44ad79e8f7b2b4054e9ae1705f62de5504a"

# MySQL Configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'library_tjg'

mysql = mysql.connector.connect(
    host=app.config['MYSQL_HOST'],
    user=app.config['MYSQL_USER'],
    password=app.config['MYSQL_PASSWORD'],
    database=app.config['MYSQL_DB']
)


#GUEST PAGE

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'status' not in session:
           return render_template('guest/home_page.html')
        return f(*args, **kwargs)
    return decorated_function


@app.route('/')
def home_page():
    session.clear()
    return render_template('guest/home_page.html')


@app.route('/search', methods=['GET'])
def search():
    _search_data = request.args.get('search')
    # Menampilkan data buku dari text pencarian dalam penulis atau judul buku
    
    cursor = mysql.cursor()
    search_term = "%" + _search_data + "%"
    sql_query = "SELECT * FROM buku WHERE penulis LIKE %s OR Judul LIKE %s ;"
    cursor.execute(sql_query, (search_term, search_term))
    data = cursor.fetchall()
    n = len(data)
    cursor.close()
    return render_template('guest/show_books.html', data_buku=data, n=n)

@app.route('/kategori/<_kategori>', methods=['GET'])
def kategori(_kategori):
    # Menampilkan data buku berdasarkan kategori

    cursor = mysql.cursor()
    sql_query = "SELECT * FROM Buku WHERE (((Buku.Kategori)= %s));"
    cursor.execute(sql_query, (_kategori,))
    data = cursor.fetchall()
    n = len(data)
    cursor.close()
    return render_template('guest/show_books.html', data_buku=data, n=n)

@app.route('/info')
def info_page():
    return render_template('guest/info.html')

@app.route('/admin/login')
def login_page():
    return render_template('staff/login_page.html')


@app.route('/admin', methods=['POST'])
def match_data():
    _id_staff = request.form.get('Id_staff')
    _password = request.form.get('password')
    #request to service
    #check id_staff dan password ke database
    # jika mactch atau sama, next
    #jika tidak match, maka beri notif "salah id atau password"

    if _id_staff != '':
        cursor = mysql.cursor()
        sql_query = "SELECT Staff.Username, Staff.Password FROM Staff WHERE (((Staff.Username)=%s));"

        cursor.execute(sql_query, (_id_staff,))
        data = cursor.fetchall()
        cursor.close()
    else:
        return render_template('staff/invalid_login.html')
    
    if _id_staff == data[0][0] and _password == data[0][1]:
        cursor = mysql.cursor()
        cursor.execute("SELECT transaksi.Id_transaksi, transaksi.Id_anggota, anggota.Nama, transaksi.Kode_buku, transaksi.Tanggal_peminjaman, transaksi.Tanggal_pengembalian FROM anggota INNER JOIN transaksi ON anggota.Id_anggota = transaksi.Id_anggota ORDER BY transaksi.Tanggal_pengembalian ASC;")
        data = cursor.fetchall()
        n = len(data)
        cursor.close()
        denda = []
        tanggal_hari_ini = datetime.today()
        for (id_transaksi, id_anggota, nama, kode_buku, tanggal_pinjam, tgl_kembali) in data:
            year, month, day = str(tgl_kembali).split('-')
            year = int(year)
            month = int(month)
            day = int(day)
            tanggal_pengembalian = datetime(year, month, day)
            perbedaan_hari = int((tanggal_pengembalian - tanggal_hari_ini).days) + 1
            if perbedaan_hari < 0 :
                denda.append(perbedaan_hari * -2000)
            else:
                denda.append(0)
        session['status'] = 'Berhasil Login'
        return render_template('staff/transaksi.html', data_transaksi=data, n=n, denda=denda)
        
    else:
        return render_template('staff/invalid_login.html')


# # # STAFF/ADMIN PAGE
@app.route('/admin/homepage')
@login_required
def admin_home_page():
    status = session['status']
    if status == 'Berhasil Login':
        cursor = mysql.cursor()
        cursor.execute("SELECT transaksi.Id_transaksi, transaksi.Id_anggota, anggota.Nama, transaksi.Kode_buku, transaksi.Tanggal_peminjaman, transaksi.Tanggal_pengembalian FROM anggota INNER JOIN transaksi ON anggota.Id_anggota = transaksi.Id_anggota ORDER BY transaksi.Tanggal_pengembalian ASC;")
        data = cursor.fetchall()
        n = len(data)
        cursor.close()
        denda = []
        tanggal_hari_ini = datetime.today()
        for (id_transaksi, id_anggota, nama, kode_buku, tanggal_pinjam, tgl_kembali) in data:
            year, month, day = str(tgl_kembali).split('-')
            year = int(year)
            month = int(month)
            day = int(day)
            tanggal_pengembalian = datetime(year, month, day)
            perbedaan_hari = int((tanggal_pengembalian - tanggal_hari_ini).days) + 1
            if perbedaan_hari < 0 :
                denda.append(perbedaan_hari * -2000)
            else:
                denda.append(0)

        return render_template('staff/transaksi.html', data_transaksi=data, n=n, denda=denda)
    else:
        return render_template('guest/home_page.html')
    


@app.route('/admin/pinjam', methods=['POST'])
@login_required
def pinjam():
    status = session['status']
    if status == 'Berhasil Login':
        tanggal_awal = datetime.today()
        tanggal_hasil = tanggal_awal + timedelta(days=14)
        format_tgl_awal = str(tanggal_awal.year) + '-' + str(tanggal_awal.month) + '-' + str(tanggal_awal.day) 
        format_tgl_hasil = str(tanggal_hasil.year) + '-' + str(tanggal_hasil.month) + '-' + str(tanggal_hasil.day) 
        return render_template('staff/pinjam_page.html', tanggal_peminjaman = format_tgl_awal, tanggal_pengembalian = format_tgl_hasil)


@app.route('/admin/submit_peminjaman', methods=['GET'])
@login_required
def submit_peminjaman():
    status = session['status']
    if status == 'Berhasil Login':
        _id_anggota = request.args.get('ID_Anggota')
        _kode_buku = request.args.get('Kode_buku')
        tanggal_peminjaman = request.args.get('tanggal_peminjaman')
        tanggal_pengembalian = request.args.get('tanggal_pengembalian')

        #logic: id anggota itu harus di check ke database ada atau tidak, dan id anggota itu juga harus di check, 
        #jika tidak ada di database, maka peminjaman gagal dan kembali ke form itu
        # jika berhasil pinjam , maka data availble berubah menjadi NO dan kembali ke page transaksi

        cursor = mysql.cursor()
        sql_query1 = "SELECT Anggota.Id_anggota FROM Anggota WHERE (((Anggota.Id_anggota)=%s));"
        cursor.execute(sql_query1, (_id_anggota,))
        id_anggota_data = cursor.fetchall()

        sql_query2 = "SELECT Buku.Kode_buku, buku.Available FROM Buku WHERE (((Buku.Kode_buku)=%s));"
        cursor.execute(sql_query2, (_kode_buku,))
        _data = cursor.fetchall()
        cursor.close()
    
        if [] != id_anggota_data and [] != _data:
            check_available = _data[0][1]
            if check_available == 'YES':
                cursor = mysql.cursor()
                cursor.execute("SELECT COUNT(*) AS total_count FROM transaksi")
                n1 = cursor.fetchall()
                cursor.execute("SELECT COUNT(*) AS total_count FROM riwayat")
                n2 = cursor.fetchall()
                _id_transaksi = int(n1[0][0]) +  int(n2[0][0]) + 1 
                sql_query3 = '''INSERT INTO transaksi (Id_transaksi, Id_anggota, Kode_buku, Tanggal_peminjaman, Tanggal_pengembalian)
                VALUES (%s,%s ,%s,%s, %s)'''
                cursor.execute(sql_query3, (_id_transaksi, _id_anggota, _kode_buku, tanggal_peminjaman, tanggal_pengembalian))
                sql_query4 = '''UPDATE buku SET available = 'NO' WHERE Kode_buku=%s;'''
                cursor.execute(sql_query4, (_kode_buku, ))
                cursor.close()
            
                cursor = mysql.cursor()
                cursor.execute("SELECT transaksi.Id_transaksi, transaksi.Id_anggota, anggota.Nama, transaksi.Kode_buku, transaksi.Tanggal_peminjaman, transaksi.Tanggal_pengembalian FROM anggota INNER JOIN transaksi ON anggota.Id_anggota = transaksi.Id_anggota ORDER BY transaksi.Tanggal_peminjaman ASC;")
                data = cursor.fetchall()
                n = len(data)
                cursor.close()

                denda = []
                tanggal_hari_ini = datetime.today()
                for (id_transaksi, id_anggota, nama, kode_buku, tanggal_pinjam, tgl_kembali) in data:
                    year, month, day = str(tgl_kembali).split('-')
                    year = int(year)
                    month = int(month)
                    day = int(day)
                    tanggal_pengembalian = datetime(year, month, day)
                    perbedaan_hari = int((tanggal_pengembalian - tanggal_hari_ini).days) + 1
                    if perbedaan_hari < 0 :
                        denda.append(perbedaan_hari * -2000)
                    else:
                        denda.append(0)

                return render_template('staff/transaksi.html', data_transaksi=data, n=n, denda=denda)
            else:
                return render_template('staff/invalid_available.html', tanggal_peminjaman=tanggal_peminjaman, tanggal_pengembalian=tanggal_pengembalian)

        else: 
            return render_template('staff/invalid_pinjam.html', tanggal_peminjaman=tanggal_peminjaman, tanggal_pengembalian=tanggal_pengembalian)


@app.route('/admin/perpanjang/<id_transaksi>', methods=["POST"])
@login_required
def perpanjang(id_transaksi):
    status = session['status']
    if status == 'Berhasil Login':
        # select * data dari transaksi
        # insert ke data riwayat tambahkan data denda
        # lalu hapus data dari transaksi
        # lalu tambahkan lagi di transaksi baru dengan tanggal baru 
        
        cursor = mysql.cursor()
        cursor.execute("SELECT * FROM `transaksi` WHERE id_transaksi=%s", (id_transaksi,))
        data = cursor.fetchall()

        tanggal_hari_ini = datetime.today()
        year, month, day = str(data[0][4]).split('-')
        year = int(year)
        month = int(month)
        day = int(day)
        tanggal_pengembalian = datetime(year, month, day)
        perbedaan_hari = int((tanggal_pengembalian - tanggal_hari_ini).days) + 1
        if perbedaan_hari < 0 :
            denda = (perbedaan_hari * -2000)
        else:
            denda = 0

        print(data, denda)
        sql_query4= "INSERT INTO riwayat (Id_transaksi, Id_anggota, Kode_buku, Tanggal_peminjaman, Tanggal_pengembalian, Denda) VALUES(%s, %s, %s, %s, %s, %s);"
        
        cursor.execute(sql_query4, (data[0][0], data[0][1], data[0][2], str(data[0][3]), str(data[0][4]), denda))

        sql_query6 = "DELETE FROM transaksi WHERE Id_transaksi = %s;"
        cursor.execute(sql_query6, (id_transaksi,))
        cursor.close()

        cursor = mysql.cursor()
        cursor.execute("SELECT COUNT(*) AS total_count FROM transaksi")
        n1 = cursor.fetchall()
        cursor.execute("SELECT COUNT(*) AS total_count FROM riwayat")
        n2 = cursor.fetchall()
        _id_transaksi = int(n1[0][0]) +  int(n2[0][0]) + 1 
        sql_query7 = '''INSERT INTO transaksi (Id_transaksi, Id_anggota, Kode_buku, Tanggal_peminjaman, Tanggal_pengembalian)
        VALUES (%s,%s ,%s,%s, %s)'''
        tanggal_hasil = tanggal_hari_ini + timedelta(days=14)
        format_tgl_awal = str(tanggal_hari_ini.year) + '-' + str(tanggal_hari_ini.month) + '-' + str(tanggal_hari_ini.day) 
        format_tgl_hasil = str(tanggal_hasil.year) + '-' + str(tanggal_hasil.month) + '-' + str(tanggal_hasil.day) 
        cursor.execute(sql_query7,(_id_transaksi, data[0][1], data[0][2], format_tgl_awal, format_tgl_hasil) )

        ### KEMBALI KE PAGE TRANSAKSI
        cursor = mysql.cursor()
        cursor.execute("SELECT transaksi.Id_transaksi, transaksi.Id_anggota, anggota.Nama, transaksi.Kode_buku, transaksi.Tanggal_peminjaman, transaksi.Tanggal_pengembalian FROM anggota INNER JOIN transaksi ON anggota.Id_anggota = transaksi.Id_anggota ORDER BY transaksi.Tanggal_pengembalian ASC;")
        data = cursor.fetchall()
        n = len(data)
        cursor.close()
        denda = []
        tanggal_hari_ini = datetime.today()
        for (id_transaksi, id_anggota, nama, kode_buku, tanggal_pinjam, tgl_kembali) in data:
            year, month, day = str(tgl_kembali).split('-')
            year = int(year)
            month = int(month)
            day = int(day)
            tanggal_pengembalian = datetime(year, month, day)
            perbedaan_hari = int((tanggal_pengembalian - tanggal_hari_ini).days) + 1
            if perbedaan_hari < 0 :
                denda.append(perbedaan_hari * -2000)
            else:
                denda.append(0)

        return render_template('staff/transaksi.html', data_transaksi=data, n=n, denda=denda)


@app.route('/admin/pengembalian/<id_transaksi>', methods=["POST"])
@login_required
def pengembalian(id_transaksi):
    status = session['status']
    if status == 'Berhasil Login':
        # select * data dari transaksi
        # insert ke data riwayat tambahkan data denda
        # ubah available buku menjadi YES
        # lalu hapus data dari transaksi
        cursor = mysql.cursor()
        cursor.execute("SELECT * FROM `transaksi` WHERE id_transaksi=%s", (id_transaksi,))
        data = cursor.fetchall()

        tanggal_hari_ini = datetime.today()
        year, month, day = str(data[0][4]).split('-')
        year = int(year)
        month = int(month)
        day = int(day)
        tanggal_pengembalian = datetime(year, month, day)
        perbedaan_hari = int((tanggal_pengembalian - tanggal_hari_ini).days) + 1
        if perbedaan_hari < 0 :
            denda = (perbedaan_hari * -2000)
        else:
            denda = 0

        print(data, denda)
        sql_query4= "INSERT INTO riwayat (Id_transaksi, Id_anggota, Kode_buku, Tanggal_peminjaman, Tanggal_pengembalian, Denda) VALUES(%s, %s, %s, %s, %s, %s);"
        
        cursor.execute(sql_query4, (data[0][0], data[0][1], data[0][2], str(data[0][3]), str(data[0][4]), denda))

        sql_query5 = "UPDATE buku SET available = 'YES' WHERE Kode_buku=%s;"
        cursor.execute(sql_query5, (data[0][2], ))

        sql_query6 = "DELETE FROM transaksi WHERE Id_transaksi = %s;"
        cursor.execute(sql_query6, (id_transaksi,))
        cursor.close()

        ### KEMBALI KE PAGE TRANSAKSI
        cursor = mysql.cursor()
        cursor.execute("SELECT transaksi.Id_transaksi, transaksi.Id_anggota, anggota.Nama, transaksi.Kode_buku, transaksi.Tanggal_peminjaman, transaksi.Tanggal_pengembalian FROM anggota INNER JOIN transaksi ON anggota.Id_anggota = transaksi.Id_anggota ORDER BY transaksi.Tanggal_pengembalian ASC;")
        data = cursor.fetchall()
        n = len(data)
        cursor.close()
        denda = []
        tanggal_hari_ini = datetime.today()
        for (id_transaksi, id_anggota, nama, kode_buku, tanggal_pinjam, tgl_kembali) in data:
            year, month, day = str(tgl_kembali).split('-')
            year = int(year)
            month = int(month)
            day = int(day)
            tanggal_pengembalian = datetime(year, month, day)
            perbedaan_hari = int((tanggal_pengembalian - tanggal_hari_ini).days) + 1
            if perbedaan_hari < 0 :
                denda.append(perbedaan_hari * -2000)
            else:
                denda.append(0)

        return render_template('staff/transaksi.html', data_transaksi=data, n=n, denda=denda)
        ### 


@app.route('/admin/buku')
@login_required
def admin_buku_page():
    status = session['status']
    if status == 'Berhasil Login':
        #service
        #dapatkan data semua buku yang ada
        cursor = mysql.cursor()
        cursor.execute("SELECT * FROM buku")
        data = cursor.fetchall()
        n = len(data)
        cursor.close()
        return render_template('staff/buku_page.html', data_buku = data, n=n)

@app.route('/admin/tambah_buku', methods=['POST'])
@login_required
def tambah_buku():
    status = session['status']
    if status == 'Berhasil Login':
        return render_template('staff/tambah_buku.html')


@app.route('/admin/submit_tambah_buku', methods=['GET'])
@login_required
def submit_tambah_buku():
    status = session['status']
    if status == 'Berhasil Login':
        kode_buku = request.args.get('Kode_buku')
        kategori = request.args.get('kategori')
        penulis = request.args.get('penulis')
        judul = request.args.get('judul')
        available = request.args.get('available')

        # Validasi input
        if not kode_buku or not kategori or not penulis or not judul:
            error_message = "Semua kolom harus diisi"
            return render_template('staff/invalid_buku_sudah_ada.html', data_buku=None, n=0, error_message=error_message)

        # Cek apakah kode buku sudah ada di database
        cursor = mysql.cursor()
        cursor.execute("SELECT COUNT(*) FROM Buku WHERE Kode_buku = %s", (kode_buku,))
        kode_buku_exists = cursor.fetchone()[0]
        cursor.close()

        if kode_buku_exists > 0:
            error_message = "Kode buku sudah digunakan"
            return render_template('staff/invalid_buku_sudah_ada.html', data_buku=None, n=0, error_message=error_message)

        cursor = mysql.cursor()
        # Query untuk menambah buku ke database
        sql_query = "INSERT INTO Buku (Kode_buku, Kategori, Penulis, Judul, Available) VALUES (%s, %s, %s, %s, %s)"
        cursor.execute(sql_query, (kode_buku, kategori, penulis, judul, available))
        mysql.commit()  # Simpan perubahan ke database
        cursor.close()

        cursor = mysql.cursor()
        cursor.execute("SELECT * FROM buku WHERE Kode_buku IS NOT NULL AND Kategori IS NOT NULL AND Penulis IS NOT NULL AND Judul IS NOT NULL")
        data = cursor.fetchall()
        n = len(data)
        cursor.close()

        return render_template('staff/buku_page.html', data_buku=data, n=n)
    else:
        return render_template('guest/home_page.html')



@app.route('/admin/edit_buku/<kode_buku>', methods=['POST'])
@login_required
def edit_buku(kode_buku):
    status = session['status']
    if status == 'Berhasil Login':    
        cursor = mysql.cursor()
        cursor.execute("SELECT * FROM buku where Kode_buku = %s", (kode_buku,))
        data = cursor.fetchall()
        n = len(data)
        cursor.close()

        return render_template('staff/edit_buku.html', Kode_buku=kode_buku, data_buku=data, n=n)
    else:
        return render_template('guest/home_page.html')



@app.route('/admin/submit_edit_buku/<kode_buku>', methods=['GET'])
@login_required
def submit_edit_buku(kode_buku):
    status = session['status']
    if status == 'Berhasil Login':
        available = request.args.get('available')

        cursor = mysql.cursor()

        sql_query = "UPDATE Buku SET Available=%s WHERE Kode_buku=%s"
        cursor.execute(sql_query, (available, kode_buku))
        mysql.commit()  # Simpan perubahan ke database
        cursor.close()

        # Sesuaikan query di bawah sesuai dengan data yang ingin Anda ambil
        cursor = mysql.cursor()
        cursor.execute("SELECT * FROM buku WHERE Available IS NOT NULL")
        data = cursor.fetchall()
        n = len(data)
        cursor.close()

        return render_template('staff/buku_page.html', data_buku=data, n=n)
    else:
        return render_template('guest/home_page.html')



@app.route('/admin/riwayat')
@login_required
def admin_riwayat_page():
    status = session['status']
    if status == 'Berhasil Login':
        #dapatkan data riwayat buku yang pernah dipinjam
        cursor = mysql.cursor()
        cursor.execute("SELECT * FROM riwayat ORDER BY Id_transaksi DESC;")
        data = cursor.fetchall()
        n = len(data)
        cursor.close()
        return render_template('staff/riwayat.html', data=data, n=n) 
    else:
        return render_template('guest/home_page.html')


    

@app.route('/admin/view_member')
@login_required
def admin_member_page():
    status = session['status']
    if status == 'Berhasil Login':
        cursor = mysql.cursor()
        cursor.execute("SELECT * FROM anggota;")
        data = cursor.fetchall()
        n = len(data)
        cursor.close()
        return render_template('staff/view_member.html', data=data, n=n) 
    else:
        return render_template('guest/home_page.html')


@app.route('/admin/view_staff')
@login_required
def admin_staff_page():
    status = session['status']
    if status == 'Berhasil Login':        
        #service
        #dapatkan data dari staff yang ada
        cursor = mysql.cursor()
        cursor.execute("SELECT staff.Username, staff.Nama, staff.Jabatan FROM staff; ")
        data = cursor.fetchall()
        n = len(data)
        cursor.close()
        return render_template('staff/view_staff.html',  data=data, n=n)
    else:
        return render_template('guest/home_page.html')


@app.route('/admin/register_member')
@login_required
def admin_register_member_page():
    status = session['status']
    if status == 'Berhasil Login':
        return render_template('staff/register_member.html')
    else:
        return render_template('guest/home_page.html')



@app.route('/admin/register_member/submit', methods=['GET'])
@login_required
def registrasi_member_submit():
    status = session['status']
    if status == 'Berhasil Login':
        _id_anggota = request.args.get('ID_anggota')
        _nama = request.args.get('nama')
        _email = request.args.get('email')

        # Validasi input
        if not _id_anggota or not _nama or not _email:
            return render_template('staff/invalid_register_member.html')

        # Cek apakah ID anggota sudah ada di database
        cursor = mysql.cursor()
        cursor.execute("SELECT anggota.Id_anggota FROM anggota WHERE anggota.Id_anggota = %s", (_id_anggota,))
        existing_id = cursor.fetchone()
        cursor.close()

        if existing_id:
            return render_template('staff/invalid_register_member.html')

        # Insert data member baru ke database
        cursor = mysql.cursor()
        cursor.execute("INSERT INTO Anggota (Id_anggota, Nama, Email) VALUES (%s, %s, %s);", (_id_anggota, _nama, _email))
        cursor.close()

        cursor = mysql.cursor()
        cursor.execute("SELECT * FROM anggota;")
        data = cursor.fetchall()
        n = len(data)
        cursor.close()

        return render_template('staff/view_member.html', data=data, n=n)
    else:
        return render_template('guest/home_page.html')




@app.route('/admin/register_staff')
@login_required
def admin_register_staff_page():
    status = session['status']
    if status == 'Berhasil Login':    
        return render_template('staff/register_staff.html')
    else:
        return render_template('guest/home_page.html')


@app.route('/admin/register_staff/submit', methods=['GET'])
@login_required
def registrasi_staff_submit():
    status = session['status']
    if status == 'Berhasil Login':
        Username = request.args.get('Username')
        password = request.args.get('password')
        nama = request.args.get('nama')
        jabatan = request.args.get('jabatan')

        # Validasi input
        if not Username or not password or not nama or not jabatan:
            return render_template('staff/invalid_register_staff.html')

        # Cek apakah username sudah ada di database
        cursor = mysql.cursor()
        cursor.execute("SELECT staff.Username FROM staff WHERE staff.Username = %s", (Username,))
        existing_username = cursor.fetchone()
        cursor.close()

        if existing_username:
            return render_template('staff/invalid_register_staff.html')

        # Insert data staff baru ke database
        cursor = mysql.cursor()
        cursor.execute("INSERT INTO staff (Username, Password, Nama, Jabatan) VALUES (%s, %s, %s, %s);", (Username, password, nama, jabatan))
        cursor.close()

        cursor = mysql.cursor()
        cursor.execute("SELECT staff.Username, staff.Nama, staff.Jabatan FROM staff;")
        data = cursor.fetchall()
        n = len(data)
        cursor.close()

        return render_template('staff/view_staff.html', data=data, n=n)
    else:
        return render_template('guest/home_page.html')

if __name__ == '__main__':
    
    app.run(debug = True)