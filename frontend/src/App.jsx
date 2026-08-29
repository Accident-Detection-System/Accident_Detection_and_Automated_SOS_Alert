import React, {
  useEffect,
  useRef,
  useState
} from 'react';

import {
  Activity,
  AlertTriangle,
  BarChart3,
  Camera,
  CheckCircle2,
  ChevronRight,
  Crosshair,
  FileVideo,
  Hospital,
  LogOut,
  MapPin,
  Menu,
  Radio,
  ShieldCheck,
  Siren,
  Upload,
  UserRound,
  X,
  Zap
} from 'lucide-react';

import {
  api,
  API_URL,
  mediaUrl
} from './lib/api';

import {
  AreaChart,
  Area,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend
} from 'recharts';


/* =========================================================
   CONSTANTS
========================================================= */

const TOKEN_KEY = 'accidentguard_token';
const USER_KEY = 'accidentguard_user';

const vehicleHint =
  'Person + vehicle overlap heuristic';


/* =========================================================
   AUTH HELPERS
========================================================= */

function saveAuth(data) {
  localStorage.setItem(
    TOKEN_KEY,
    data.token
  );

  localStorage.setItem(
    USER_KEY,
    JSON.stringify(data.user)
  );
}


function clearAuth() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}


function getStoredUser() {
  try {
    return JSON.parse(
      localStorage.getItem(USER_KEY) || 'null'
    );
  } catch {
    return null;
  }
}


/* =========================================================
   MAIN APP
========================================================= */

export default function App() {

  const [user, setUser] = useState(
    getStoredUser()
  );

  const [mode, setMode] = useState('login');

  const [authRole, setAuthRole] =
    useState('hospital');

  const [tab, setTab] =
    useState('overview');

  const [notice, setNotice] =
    useState(null);

  const [socket, setSocket] =
    useState(null);

  const [incoming, setIncoming] =
    useState(null);

  const [socketEvent, setSocketEvent] =
    useState(null);


  const notify = (type, text) => {

    setNotice({
      type,
      text
    });

    setTimeout(
      () => setNotice(null),
      5000
    );
  };


  /* ---------------------------------------------------------
     Validate stored login
  --------------------------------------------------------- */

  useEffect(() => {

    if (!user) return;

    api('/api/me')
      .catch(() => {

        clearAuth();
        setUser(null);

      });

  }, []);


  /* ---------------------------------------------------------
     WebSocket
  --------------------------------------------------------- */

  useEffect(() => {

    if (!user) return;

    const token =
      localStorage.getItem(TOKEN_KEY);

    if (!token) return;


    const wsBase =
      API_URL.replace(/^http/, 'ws');


    const ws =
      new WebSocket(
        `${wsBase}/ws?token=${encodeURIComponent(token)}`
      );


    ws.onmessage = event => {

      try {

        const msg =
          JSON.parse(event.data);

        setSocketEvent(msg);


        if (
          msg.type === 'accident_alert' ||
          msg.type === 'accident_confirmed'
        ) {

          setIncoming(msg.data);

        }

      } catch {
        // Ignore malformed websocket messages
      }

    };


    ws.onerror = () => {
      // WebSocket errors are handled by the UI state
    };


    setSocket(ws);


    return () => {

      try {
        ws.close();
      } catch {
        // Ignore close errors
      }

    };

  }, [user]);


  /* ---------------------------------------------------------
     Authentication screen
  --------------------------------------------------------- */

  if (!user) {

    return (
      <AuthScreen
        role={authRole}
        setRole={setAuthRole}
        mode={mode}
        setMode={setMode}
        onAuth={data => {

          saveAuth(data);

          setUser(data.user);

          setTab('overview');

        }}
        notify={notify}
        notice={notice}
      />
    );

  }


  /* ---------------------------------------------------------
     Dashboard
  --------------------------------------------------------- */

  return (
    <Dashboard
      user={user}
      tab={tab}
      setTab={setTab}
      onLogout={() => {

        socket?.close();

        clearAuth();

        setUser(null);

      }}
      notice={notice}
      notify={notify}
      incoming={incoming}
      setIncoming={setIncoming}
      socket={socket}
      socketEvent={socketEvent}
    />
  );
}


/* =========================================================
   AUTH SCREEN
========================================================= */

function AuthScreen({
  role,
  setRole,
  mode,
  setMode,
  onAuth,
  notify,
  notice
}) {

  const [form, setForm] =
    useState({
      name: '',
      email: '',
      password: '',
      location: '',
      phone: '',
      latitude: '',
      longitude: ''
    });


  const [loading, setLoading] =
    useState(false);


  const register =
    mode === 'register';


  const submit = async event => {

    event.preventDefault();

    setLoading(true);


    try {

      const path =
        role === 'hospital'
          ? (
              register
                ? '/api/register'
                : '/api/login'
            )
          : (
              register
                ? '/api/user/register'
                : '/api/user/login'
            );


      const body = register
        ? {
            ...form,
            latitude: form.latitude
              ? Number(form.latitude)
              : null,
            longitude: form.longitude
              ? Number(form.longitude)
              : null
          }
        : {
            email: form.email,
            password: form.password
          };


      const data =
        await api(
          path,
          {
            method: 'POST',
            body: JSON.stringify(body)
          }
        );


      onAuth(data);

    } catch (error) {

      notify(
        'error',
        error.message
      );

    } finally {

      setLoading(false);

    }

  };


  const locate = () => {

    if (!navigator.geolocation) {

      notify(
        'error',
        'Geolocation is not supported by this browser.'
      );

      return;

    }


    navigator.geolocation.getCurrentPosition(

      position => {

        setForm(current => ({
          ...current,
          latitude:
            position.coords.latitude.toFixed(6),
          longitude:
            position.coords.longitude.toFixed(6)
        }));

      },

      () => {

        notify(
          'error',
          'Location permission was not available.'
        );

      }

    );

  };


  return (
    <div className="auth-shell">

      <div className="auth-hero">

        <div className="brand">

          <span className="brand-mark">
            <Siren size={20}/>
          </span>

          <span>
            Accident
            <span>Guard</span>
          </span>

        </div>


        <div className="hero-copy">

          <div className="eyebrow">
            <ShieldCheck size={14}/>
            REAL-TIME ROAD SAFETY
          </div>


          <h1>
            Turn accident signals into
            <em> faster response.</em>
          </h1>


          <p>
            AI-assisted video detection,
            GPS-aware hospital routing,
            live CCTV monitoring and
            emergency alerts in one
            operational dashboard.
          </p>


          <div className="hero-points">

            <div>
              <CheckCircle2/>
              Automated detection
            </div>

            <div>
              <CheckCircle2/>
              Severity scoring
            </div>

            <div>
              <CheckCircle2/>
              Nearest hospitals
            </div>

          </div>

        </div>


        <div className="hero-foot">
          {vehicleHint}
        </div>

      </div>


      <div className="auth-panel">

        <div className="role-switch">

          <button
            className={
              role === 'hospital'
                ? 'active'
                : ''
            }
            onClick={() =>
              setRole('hospital')
            }
          >
            <Hospital size={17}/>
            Hospital
          </button>


          <button
            className={
              role === 'user'
                ? 'active'
                : ''
            }
            onClick={() =>
              setRole('user')
            }
          >
            <UserRound size={17}/>
            Citizen
          </button>

        </div>


        <div className="auth-card">

          <div className="auth-title">

            <div className="icon-tile">
              <Zap/>
            </div>

            <div>

              <h2>
                {
                  register
                    ? 'Create your account'
                    : 'Welcome back'
                }
              </h2>

              <p>
                {
                  register
                    ? 'Set up your emergency response profile.'
                    : 'Sign in to your safety operations console.'
                }
              </p>

            </div>

          </div>


          <form onSubmit={submit}>

            {register && (

              <input
                placeholder="Full name"
                value={form.name}
                onChange={e =>
                  setForm({
                    ...form,
                    name: e.target.value
                  })
                }
                required
              />

            )}


            <input
              type="email"
              placeholder="Email address"
              value={form.email}
              onChange={e =>
                setForm({
                  ...form,
                  email: e.target.value
                })
              }
              required
            />


            <input
              type="password"
              placeholder="Password (min. 6 characters)"
              value={form.password}
              onChange={e =>
                setForm({
                  ...form,
                  password: e.target.value
                })
              }
              required
            />


            {register && (

              <>
                <input
                  placeholder="Phone"
                  value={form.phone}
                  onChange={e =>
                    setForm({
                      ...form,
                      phone: e.target.value
                    })
                  }
                />


                {role === 'hospital' && (

                  <input
                    placeholder="Hospital location"
                    value={form.location}
                    onChange={e =>
                      setForm({
                        ...form,
                        location: e.target.value
                      })
                    }
                  />

                )}


                <div className="gps-inputs">

                  <input
                    type="number"
                    step="any"
                    placeholder="Latitude"
                    value={form.latitude}
                    onChange={e =>
                      setForm({
                        ...form,
                        latitude: e.target.value
                      })
                    }
                  />


                  <input
                    type="number"
                    step="any"
                    placeholder="Longitude"
                    value={form.longitude}
                    onChange={e =>
                      setForm({
                        ...form,
                        longitude: e.target.value
                      })
                    }
                  />

                </div>


                <button
                  type="button"
                  className="ghost-btn"
                  onClick={locate}
                >
                  <MapPin size={15}/>
                  Use my GPS
                </button>

              </>

            )}


            <button
              className="primary-btn"
              disabled={loading}
            >

              {loading ? (

                <span className="spinner"/>

              ) : (

                <>
                  {
                    register
                      ? 'Create account'
                      : 'Sign in'
                  }

                  <ChevronRight size={17}/>
                </>

              )}

            </button>

          </form>


          <div className="auth-switch">

            {
              register
                ? 'Already have an account?'
                : 'New here?'
            }

            {' '}

            <button
              onClick={() =>
                setMode(
                  register
                    ? 'login'
                    : 'register'
                )
              }
            >
              {
                register
                  ? 'Sign in'
                  : 'Create account'
              }
            </button>

          </div>

        </div>


        <div className="security-note">

          <ShieldCheck size={14}/>

          Credentials are stored securely
          using bcrypt hashing.

        </div>

      </div>


      {notice && (
        <Notice notice={notice}/>
      )}

    </div>
  );
}


/* =========================================================
   DASHBOARD
========================================================= */

function Dashboard({
  user,
  tab,
  setTab,
  onLogout,
  notice,
  notify,
  incoming,
  setIncoming,
  socket,
  socketEvent
}) {

  const [
    mobileOpen,
    setMobileOpen
  ] = useState(false);


  const hospital =
    user.user_type === 'hospital';


  const nav = hospital

    ? [
        ['overview', 'Overview', Activity],
        ['upload', 'Video analysis', Upload],
        ['live', 'Live camera', Radio],
        ['alerts', 'Alerts', AlertTriangle],
        ['cameras', 'Cameras', Camera],
        ['analytics', 'Analytics', BarChart3]
      ]

    : [
        ['overview', 'Emergency', Siren],
        ['upload', 'Analyze video', Upload],
        ['live', 'Live camera', Radio]
      ];


  return (
    <div className="app-shell">

      <aside
        className={
          mobileOpen
            ? 'sidebar open'
            : 'sidebar'
        }
      >

        <div className="side-brand">

          <span className="brand-mark">
            <Siren size={18}/>
          </span>

          <span>
            Accident
            <span>Guard</span>
          </span>

        </div>


        <div className="side-caption">
          EMERGENCY INTELLIGENCE
        </div>


        <nav>

          {nav.map(
            ([id, label, Icon]) => (

              <button
                key={id}
                className={
                  tab === id
                    ? 'nav-item active'
                    : 'nav-item'
                }
                onClick={() => {

                  setTab(id);

                  setMobileOpen(false);

                }}
              >

                <Icon size={18}/>

                {label}

                {
                  id === 'alerts' &&
                  incoming
                    ? <span className="nav-dot"/>
                    : null
                }

              </button>

            )
          )}

        </nav>


        <div className="side-status">

          <span className="live-dot"/>

          AI engine online

          <div>
            YOLOv8 · FastAPI
          </div>

        </div>


        <div className="side-user">

          <div className="avatar">
            {
              user.name
                ?.slice(0, 1)
                .toUpperCase()
            }
          </div>


          <div>

            <strong>
              {user.name}
            </strong>

            <small>
              {
                hospital
                  ? 'Hospital operator'
                  : 'Citizen account'
              }
            </small>

          </div>


          <button onClick={onLogout}>
            <LogOut size={16}/>
          </button>

        </div>

      </aside>


      <main className="main-shell">

        <header className="topbar">

          <button
            className="menu-btn"
            onClick={() =>
              setMobileOpen(
                value => !value
              )
            }
          >
            <Menu/>
          </button>


          <div>

            <div className="page-kicker">

              {
                hospital
                  ? 'HOSPITAL CONTROL CENTER'
                  : 'PERSONAL SAFETY CENTER'
              }

            </div>


            <h2>
              {
                nav.find(
                  item => item[0] === tab
                )?.[1]
              }
            </h2>

          </div>


          <div className="top-actions">

            <div className="connection">

              <span className="live-dot"/>

              Live system

            </div>


            <div className="profile-chip">

              <span className="avatar small">

                {
                  user.name
                    ?.slice(0, 1)
                    .toUpperCase()
                }

              </span>

              {user.name}

            </div>

          </div>

        </header>


        <div className="content">

          {tab === 'overview' && (

            <Overview
              user={user}
              hospital={hospital}
              go={setTab}
              notify={notify}
            />

          )}


          {tab === 'upload' && (

            <UploadPage
              user={user}
              notify={notify}
            />

          )}


          {tab === 'live' && (

            <LivePage
              user={user}
              socket={socket}
              socketEvent={socketEvent}
              notify={notify}
            />

          )}


          {tab === 'alerts' && (

            <AlertsPage
              incoming={incoming}
              setIncoming={setIncoming}
              notify={notify}
            />

          )}


          {tab === 'cameras' && (

            <CamerasPage
              notify={notify}
            />

          )}


          {tab === 'analytics' && (

            <AnalyticsPage/>

          )}

        </div>

      </main>


      {incoming && (

        <IncomingAlert
          data={incoming}
          close={() =>
            setIncoming(null)
          }
        />

      )}


      {notice && (
        <Notice notice={notice}/>
      )}

    </div>
  );
}


/* =========================================================
   OVERVIEW
========================================================= */

function Overview({
  user,
  hospital,
  go,
  notify
}) {

  const [sos, setSos] =
    useState(null);


  const trigger = () => {

    if (!navigator.geolocation) {

      notify(
        'error',
        'GPS is required for SOS.'
      );

      return;

    }


    navigator.geolocation.getCurrentPosition(

      async position => {

        try {

          const result =
            await api(
              '/api/sos',
              {
                method: 'POST',
                body: JSON.stringify({
                  lat:
                    position.coords.latitude,
                  lon:
                    position.coords.longitude
                })
              }
            );


          setSos(result);

        } catch (error) {

          notify(
            'error',
            error.message
          );

        }

      },

      () => {

        notify(
          'error',
          'Allow GPS access before sending SOS.'
        );

      }

    );

  };


  return (
    <div className="page">

      <div className="hero-banner">

        <div>

          <div className="eyebrow">

            <Activity size={14}/>

            ACTIVE PROTECTION

          </div>


          <h1>

            {
              hospital
                ? 'Emergency response, at a glance.'
                : 'One tap from emergency help.'
            }

          </h1>


          <p>

            {
              hospital
                ? 'Monitor accident signals, camera feeds and response activity from one place.'
                : 'Analyze road footage or send a GPS-based emergency alert to nearby hospitals.'
            }

          </p>

        </div>


        <div className="hero-stat">

          <span>
            AI ENGINE
          </span>

          <strong>
            READY
          </strong>

          <small>
            YOLOv8 detection online
          </small>

        </div>

      </div>


      {!hospital && (

        <div className="sos-card">

          <div>

            <span className="eyebrow red">

              <Siren size={14}/>

              EMERGENCY

            </span>


            <h2>
              Need immediate help?
            </h2>


            <p>
              Your GPS location will be
              shared with the nearest
              registered hospitals.
            </p>

          </div>


          <button
            onClick={trigger}
            className="sos-btn"
          >

            <Siren/>

            SEND SOS

          </button>

        </div>

      )}


      {sos && (

        <ResultCard
          data={sos}
          title="SOS sent successfully"
        />

      )}


      <div className="metric-grid">

        <Metric
          icon={FileVideo}
          label="Video analysis"
          value="AI"
          sub="Upload footage"
          onClick={() =>
            go('upload')
          }
        />


        <Metric
          icon={Radio}
          label="Live detection"
          value="LIVE"
          sub="Camera stream"
          onClick={() =>
            go('live')
          }
        />


        {hospital ? (

          <>

            <Metric
              icon={AlertTriangle}
              label="Alerts"
              value="100"
              sub="Latest records"
              onClick={() =>
                go('alerts')
              }
            />


            <Metric
              icon={Hospital}
              label="Response"
              value="3"
              sub="Nearest hospitals"
              onClick={() =>
                go('alerts')
              }
            />

          </>

        ) : (

          <Metric
            icon={MapPin}
            label="GPS"
            value="ON"
            sub="Location aware"
          />

        )}

      </div>


      <div className="info-grid">

        <InfoCard
          icon={ShieldCheck}
          title="How detection works"
          text="YOLOv8 identifies road users; the backend evaluates person/vehicle bounding-box overlap and calculates a severity score."
        />


        <InfoCard
          icon={Zap}
          title="Response workflow"
          text="A confirmed event is saved, a screenshot/clip is created, nearby hospitals are ranked by distance and email alerts can be sent."
        />

      </div>

    </div>
  );
}


/* =========================================================
   METRIC
========================================================= */

function Metric({
  icon: Icon,
  label,
  value,
  sub,
  onClick
}) {

  return (
    <button
      className="metric"
      onClick={onClick}
    >

      <div className="metric-icon">
        <Icon/>
      </div>


      <div>

        <span>
          {label}
        </span>

        <strong>
          {value}
        </strong>

        <small>
          {sub}
        </small>

      </div>


      <ChevronRight/>

    </button>
  );
}


/* =========================================================
   INFO CARD
========================================================= */

function InfoCard({
  icon: Icon,
  title,
  text
}) {

  return (
    <div className="info-card">

      <div className="info-icon">
        <Icon/>
      </div>


      <div>

        <h3>
          {title}
        </h3>

        <p>
          {text}
        </p>

      </div>

    </div>
  );
}


/* =========================================================
   VIDEO UPLOAD PAGE
========================================================= */

function UploadPage({
  user,
  notify
}) {

  const [file, setFile] =
    useState(null);

  const [cameras, setCameras] =
    useState([]);

  const [camera, setCamera] =
    useState('');

  const [gps, setGps] =
    useState({
      lat: null,
      lon: null
    });

  const [job, setJob] =
    useState(null);

  const input =
    useRef();


  useEffect(() => {

    if (
      user.user_type !== 'hospital'
    ) {
      return;
    }


    api('/api/cameras/my')
      .then(data =>
        setCameras(
          Array.isArray(data)
            ? data
            : []
        )
      )
      .catch(() => {});

  }, [user.user_type]);


  const chooseGps = () => {

    if (!navigator.geolocation) {

      notify(
        'error',
        'Geolocation is not supported.'
      );

      return;

    }


    navigator.geolocation.getCurrentPosition(

      position => {

        setGps({
          lat:
            position.coords.latitude,
          lon:
            position.coords.longitude
        });

      },

      () => {

        notify(
          'error',
          'GPS permission denied.'
        );

      }

    );

  };


  const upload = async () => {

    if (!file) return;


    if (
      user.user_type === 'hospital' &&
      !camera
    ) {

      notify(
        'error',
        'Select a camera first.'
      );

      return;

    }


    try {

      const formData =
        new FormData();


      formData.append(
        'video',
        file
      );


      if (camera) {

        formData.append(
          'camera_id',
          camera
        );

      }


      if (gps.lat != null) {

        formData.append(
          'gps_lat',
          gps.lat
        );

        formData.append(
          'gps_lon',
          gps.lon
        );

      }


      const result =
        await api(
          '/api/upload',
          {
            method: 'POST',
            body: formData
          }
        );


      setJob({
        status: 'processing',
        progress: 0,
        alert_id:
          result.alert_id
      });


      const timer =
        setInterval(
          async () => {

            try {

              const status =
                await api(
                  `/api/status/${result.alert_id}`
                );


              setJob({
                ...status,
                alert_id:
                  result.alert_id
              });


              if (
                ['done', 'error']
                  .includes(status.status)
              ) {

                clearInterval(timer);

              }

            } catch (error) {

              clearInterval(timer);

              notify(
                'error',
                error.message
              );

            }

          },
          1200
        );

    } catch (error) {

      notify(
        'error',
        error.message
      );

    }

  };


  return (
    <div className="page narrow">

      <div className="section-head">

        <div>

          <div className="eyebrow">

            <FileVideo size={14}/>

            VIDEO INTELLIGENCE

          </div>


          <h1>
            Analyze accident footage
          </h1>


          <p>
            Upload a road video and
            let the detection engine
            scan it frame by frame.
          </p>

        </div>

      </div>


      <div className="analysis-layout">

        <div className="card">

          <div
            className="dropzone"
            onClick={() =>
              input.current?.click()
            }
          >

            <input
              ref={input}
              type="file"
              hidden
              accept="video/*"
              onChange={event =>
                setFile(
                  event.target.files?.[0] ||
                  null
                )
              }
            />


            <div className="upload-orb">
              <Upload/>
            </div>


            <h3>

              {
                file
                  ? file.name
                  : 'Drop your video here'
              }

            </h3>


            <p>

              {
                file
                  ? 'Ready to analyze'
                  : 'MP4, MOV, AVI, MKV or WEBM · up to 250 MB'
              }

            </p>


            {file && (

              <span className="file-size">

                {
                  (
                    file.size /
                    1024 /
                    1024
                  ).toFixed(1)
                }

                {' '}MB

              </span>

            )}

          </div>


          {user.user_type === 'hospital' && (

            <label className="field-label">

              Camera source

              <select
                value={camera}
                onChange={e =>
                  setCamera(e.target.value)
                }
              >

                <option value="">
                  Choose camera
                </option>


                {cameras.map(cameraItem => (

                  <option
                    key={cameraItem.id}
                    value={cameraItem.id}
                  >

                    {cameraItem.name}
                    {' · '}
                    {
                      cameraItem.location ||
                      'No location'
                    }

                  </option>

                ))}

              </select>

            </label>

          )}


          <div className="gps-row-card">

            <div>

              <strong>
                GPS location
              </strong>

              <span>

                {
                  gps.lat
                    ? `${gps.lat.toFixed(5)}, ${gps.lon.toFixed(5)}`
                    : 'Optional but recommended'
                }

              </span>

            </div>


            <button onClick={chooseGps}>

              <MapPin size={15}/>

              Get location

            </button>

          </div>


          <button
            className="primary-btn big"
            onClick={upload}
            disabled={
              !file ||
              job?.status === 'processing'
            }
          >

            {
              job?.status === 'processing'
                ? (
                  <>
                    <span className="spinner"/>
                    Analyzing…
                  </>
                )
                : (
                  <>
                    Start AI analysis
                    <ChevronRight/>
                  </>
                )
            }

          </button>

        </div>


        <div className="card process-card">

          <div className="card-label">
            PROCESS STATUS
          </div>


          {!job ? (

            <EmptyState
              icon={Crosshair}
              title="Ready when you are"
              text="Choose a video to begin. Results appear here while the backend processes frames."
            />

          ) : (

            <JobStatus job={job}/>

          )}


          <div className="engine-note">

            <ShieldCheck size={15}/>

            <span>

              <strong>
                Detection engine
              </strong>

              <br/>

              {vehicleHint}
              {' · '}
              threshold 0.37

            </span>

          </div>

        </div>

      </div>

    </div>
  );
}


/* =========================================================
   JOB STATUS
========================================================= */

function JobStatus({
  job
}) {

  return (
    <div>

      <div className="job-icon">

        {
          job.accident
            ? <AlertTriangle/>
            : <Activity/>
        }

      </div>


      <h3>

        {
          job.status === 'error'
            ? 'Analysis failed'
            : job.accident
              ? 'Accident detected'
              : 'Analyzing footage'
        }

      </h3>


      <p>

        {
          job.status === 'done'
            ? (
                job.accident
                  ? 'Emergency evidence was saved and hospitals can be notified.'
                  : 'No accident signal was confirmed.'
              )
            : `${job.progress || 0}% complete`
        }

      </p>


      <div className="progress">

        <span
          style={{
            width:
              `${job.progress || 0}%`
          }}
        />

      </div>


      {job.accident && (

        <div className="result-mini">

          <Severity
            severity={job.severity}
          />


          {job.location && (

            <span>

              <MapPin size={14}/>

              {job.location}

            </span>

          )}


          {job.screenshot && (

            <img
              src={
                mediaUrl(
                  job.screenshot
                )
              }
              alt="Accident evidence"
            />

          )}

        </div>

      )}

    </div>
  );
}


/* =========================================================
   LIVE CAMERA PAGE
========================================================= */

function LivePage({
  user,
  socket,
  socketEvent,
  notify
}) {

  const video =
    useRef(null);

  const canvas =
    useRef(null);

  const timer =
    useRef(null);


  const [active, setActive] =
    useState(false);


  const [status, setStatus] =
    useState({
      detected: false
    });


  const [gps, setGps] =
    useState(null);


  const [cameras, setCameras] =
    useState([]);


  const [cameraId, setCameraId] =
    useState('');


  const [loadingCameras, setLoadingCameras] =
    useState(false);


  const [socketReady, setSocketReady] =
    useState(
      socket?.readyState ===
      WebSocket.OPEN
    );


  /* ---------------------------------------------------------
     Check WebSocket state
  --------------------------------------------------------- */

  useEffect(() => {

    const check = () => {

      setSocketReady(
        socket?.readyState ===
        WebSocket.OPEN
      );

    };


    check();


    const id =
      setInterval(
        check,
        500
      );


    return () =>
      clearInterval(id);

  }, [socket]);


  /* ---------------------------------------------------------
     Load cameras
  --------------------------------------------------------- */

  useEffect(() => {

    if (
      user?.user_type !==
      'hospital'
    ) {
      return;
    }


    setLoadingCameras(true);


    api('/api/cameras/my')

      .then(data => {

        const list =
          Array.isArray(data)
            ? data
            : [];


        setCameras(list);


        if (
          list.length &&
          !cameraId
        ) {

          setCameraId(
            String(list[0].id)
          );

        }

      })

      .catch(error => {

        notify(
          'error',
          `Could not load cameras: ${error.message}`
        );

      })

      .finally(() => {

        setLoadingCameras(false);

      });

  }, [user?.user_type]);


  /* ---------------------------------------------------------
     Detection events
  --------------------------------------------------------- */

  useEffect(() => {

    if (
      socketEvent?.type ===
      'detection_result'
    ) {

      setStatus(
        socketEvent.data ||
        {
          detected: false
        }
      );

    }


    if (
      socketEvent?.type ===
      'accident_confirmed' &&
      socketEvent.data
    ) {

      setStatus({
        detected: true,
        severity:
          socketEvent.data.severity
      });

    }

  }, [socketEvent]);


  /* ---------------------------------------------------------
     Cleanup camera
  --------------------------------------------------------- */

  const cleanupStream = () => {

    if (timer.current) {

      clearInterval(
        timer.current
      );

    }


    timer.current = null;


    const stream =
      video.current?.srcObject;


    if (stream) {

      stream
        .getTracks()
        .forEach(
          track =>
            track.stop()
        );

    }


    if (video.current) {

      video.current.srcObject =
        null;

    }

  };


  /* ---------------------------------------------------------
     Stop detection
  --------------------------------------------------------- */

  const stop = () => {

    if (timer.current) {

      clearInterval(
        timer.current
      );

    }


    timer.current = null;


    cleanupStream();


    if (
      socket?.readyState ===
      WebSocket.OPEN
    ) {

      socket.send(
        JSON.stringify({
          type: 'stop_live'
        })
      );

    }


    setActive(false);


    setStatus({
      detected: false
    });

  };


  /* ---------------------------------------------------------
     Start detection
  --------------------------------------------------------- */

  const start = async () => {

    try {

      if (
        !socket ||
        !socketReady ||
        socket.readyState !==
          WebSocket.OPEN
      ) {

        notify(
          'error',
          'Live AI connection is not ready. Please wait a moment and try again.'
        );

        return;

      }


      if (
        user?.user_type ===
          'hospital' &&
        !cameraId
      ) {

        notify(
          'error',
          'Please select a registered camera first.'
        );

        return;

      }


      if (
        !navigator.mediaDevices?.getUserMedia
      ) {

        throw new Error(
          'Camera access is not supported by this browser.'
        );

      }


      const stream =
        await navigator.mediaDevices.getUserMedia({
          video: {
            facingMode:
              'environment'
          },
          audio: false
        });


      if (!video.current) {

        stream
          .getTracks()
          .forEach(
            track =>
              track.stop()
          );

        return;

      }


      video.current.srcObject =
        stream;


      await video.current.play();


      setActive(true);


      setStatus({
        detected: false
      });


      socket.send(
        JSON.stringify({
          type: 'start_live',
          camera_id:
            user?.user_type ===
            'hospital'
              ? Number(cameraId)
              : null
        })
      );


      /* -----------------------------------------------------
         GPS
      ----------------------------------------------------- */

      if (navigator.geolocation) {

        navigator.geolocation.getCurrentPosition(

          position => {

            const location = {
              lat:
                position.coords.latitude,
              lon:
                position.coords.longitude
            };


            setGps(location);


            if (
              socket.readyState ===
              WebSocket.OPEN
            ) {

              socket.send(
                JSON.stringify({
                  type: 'gps_update',
                  ...location
                })
              );

            }

          },

          () => {

            notify(
              'error',
              'Camera started, but GPS permission was not granted.'
            );

          }

        );

      }


      /* -----------------------------------------------------
         Capture frames
      ----------------------------------------------------- */

      timer.current =
        setInterval(
          () => {

            if (
              !canvas.current ||
              !video.current ||
              video.current.readyState < 2 ||
              socket.readyState !==
                WebSocket.OPEN
            ) {

              return;

            }


            const c =
              canvas.current;


            const width =
              Math.min(
                640,
                video.current
                  .videoWidth ||
                  480
              );


            const height =
              Math.max(
                1,
                Math.round(
                  width *
                  (
                    video.current
                      .videoHeight ||
                    360
                  ) /
                  (
                    video.current
                      .videoWidth ||
                    480
                  )
                )
              );


            c.width =
              width;

            c.height =
              height;


            const ctx =
              c.getContext(
                '2d'
              );


            if (!ctx) return;


            ctx.drawImage(
              video.current,
              0,
              0,
              width,
              height
            );


            c.toBlob(
              blob => {

                if (
                  !blob ||
                  socket.readyState !==
                    WebSocket.OPEN
                ) {

                  return;

                }


                const reader =
                  new FileReader();


                reader.onload = () => {

                  if (
                    socket.readyState ===
                    WebSocket.OPEN
                  ) {

                    socket.send(
                      JSON.stringify({
                        type:
                          'live_frame',
                        frame:
                          String(
                            reader.result
                          ).split(',')[1]
                      })
                    );

                  }

                };


                reader.readAsDataURL(
                  blob
                );

              },
              'image/jpeg',
              0.55
            );

          },
          700
        );

    } catch (error) {

      cleanupStream();

      setActive(false);


      notify(
        'error',
        error?.message ||
        'Camera permission is required.'
      );

    }

  };


  /* ---------------------------------------------------------
     Cleanup when leaving page
  --------------------------------------------------------- */

  useEffect(() => {

    return () => {

      cleanupStream();

    };

  }, []);


  const selectedCamera =
    cameras.find(
      camera =>
        String(camera.id) ===
        String(cameraId)
    );


  return (
    <div className="page narrow">

      {/* =====================================================
          HEADER
      ====================================================== */}

      <div className="section-head">

        <div>

          <div className="eyebrow">

            <Radio size={14}/>

            LIVE COMPUTER VISION

          </div>


          <h1>
            Live camera detection
          </h1>


          <p>
            Stream your camera to
            FastAPI and receive
            real-time accident signals.
          </p>

        </div>


        <div
          className={
            active
              ? 'live-badge active'
              : 'live-badge'
          }
        >

          <span/>

          {
            active
              ? 'DETECTION ACTIVE'
              : 'STANDBY'
          }

        </div>

      </div>


      {/* =====================================================
          CAMERA SOURCE
      ====================================================== */}

      <div
        className="card"
        style={{
          marginBottom: 16
        }}
      >

        <div className="card-label">
          CAMERA SOURCE
        </div>


        {user?.user_type ===
        'hospital' ? (

          cameras.length ? (

            <select
              value={cameraId}
              onChange={e =>
                setCameraId(
                  e.target.value
                )
              }
              disabled={active}
              style={{
                marginTop: 10,
                width: '100%'
              }}
            >

              {cameras.map(camera => (

                <option
                  key={camera.id}
                  value={camera.id}
                >

                  {camera.name}

                  {
                    camera.location
                      ? ` · ${camera.location}`
                      : ''
                  }

                </option>

              ))}

            </select>

          ) : (

            <div
              style={{
                marginTop: 10,
                color: '#8d99ac'
              }}
            >

              {
                loadingCameras
                  ? 'Loading registered cameras…'
                  : 'No registered cameras. Add one from Cameras before starting live detection.'
              }

            </div>

          )

        ) : (

          <div
            style={{
              marginTop: 10,
              color: '#8d99ac'
            }}
          >

            Your browser camera
            will be used for this
            live session.

          </div>

        )}

      </div>


      {/* =====================================================
          MAIN LIVE AREA
      ====================================================== */}

      <div
        className="live-layout"
        style={{
          display: 'grid',
          gridTemplateColumns:
            'minmax(0, 2.1fr) minmax(300px, 0.9fr)',
          gap: 16,
          alignItems: 'stretch'
        }}
      >

        {/* ===================================================
            CAMERA PANEL
        ==================================================== */}

        <div
          className="video-card"
          style={{
            position: 'relative',
            minHeight: 520,
            overflow: 'hidden',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            background:
              'linear-gradient(145deg,#0b101b,#101827)'
          }}
        >

          <video
            ref={video}
            muted
            playsInline
            style={{
              width: '100%',
              height: '100%',
              objectFit: 'cover',
              display:
                active
                  ? 'block'
                  : 'none'
            }}
          />


          <canvas
            ref={canvas}
            hidden
          />


          {/* =================================================
              CENTERED OFFLINE STATE
          ================================================== */}

          {!active && (

            <div
              className="video-placeholder"
              style={{
                position: 'absolute',
                inset: 0,
                display: 'flex',
                flexDirection:
                  'column',
                alignItems:
                  'center',
                justifyContent:
                  'center',
                textAlign:
                  'center',
                padding:
                  '40px 24px',
                gap: 12
              }}
            >

              <div
                style={{
                  width: 112,
                  height: 112,
                  borderRadius:
                    '50%',
                  display: 'flex',
                  alignItems:
                    'center',
                  justifyContent:
                    'center',
                  marginBottom: 8,
                  border:
                    '1px solid rgba(255,75,91,.55)',
                  background:
                    'rgba(255,75,91,.06)',
                  boxShadow:
                    '0 0 0 10px rgba(255,75,91,.035)'
                }}
              >

                <div
                  style={{
                    width: 76,
                    height: 76,
                    borderRadius:
                      '50%',
                    display: 'flex',
                    alignItems:
                      'center',
                    justifyContent:
                      'center',
                    border:
                      '1px solid rgba(255,75,91,.35)'
                  }}
                >

                  <Camera
                    size={38}
                    strokeWidth={1.8}
                    style={{
                      color:
                        '#ff4b5b'
                    }}
                  />

                </div>

              </div>


              <strong
                style={{
                  fontSize: 24,
                  fontWeight: 700,
                  color: '#f4f7fb',
                  letterSpacing:
                    '-0.02em'
                }}
              >

                Camera feed is offline

              </strong>


              <span
                style={{
                  maxWidth: 420,
                  color: '#8d99ac',
                  fontSize: 14,
                  lineHeight: 1.6
                }}
              >

                {
                  socketReady
                    ? 'Start live detection to begin streaming.'
                    : 'Connecting to AI engine…'
                }

              </span>


              {socketReady && (

                <button
                  className="primary-btn"
                  onClick={start}
                  disabled={
                    user?.user_type ===
                      'hospital' &&
                    !cameraId
                  }
                  style={{
                    marginTop: 12,
                    minWidth: 220,
                    justifyContent:
                      'center'
                  }}
                >

                  <Radio size={17}/>

                  Start live detection

                </button>

              )}

            </div>

          )}


          {/* =================================================
              CAMERA OVERLAY
          ================================================== */}

          <div
            className="video-overlay"
            style={{
              position: 'absolute',
              top: 16,
              left: 16,
              right: 16,
              display: 'flex',
              justifyContent:
                'space-between',
              alignItems:
                'center',
              pointerEvents:
                'none'
            }}
          >

            <span>

              <span className="live-dot"/>

              {
                active
                  ? 'LIVE'
                  : 'OFFLINE'
              }

            </span>


            {gps && (

              <span>

                <MapPin size={13}/>

                GPS linked

              </span>

            )}

          </div>

        </div>


        {/* ===================================================
            RIGHT COLUMN
        ==================================================== */}

        <div
          style={{
            display: 'flex',
            flexDirection:
              'column',
            gap: 16,
            minWidth: 0
          }}
        >

          {/* =================================================
              DETECTION STATUS
          ================================================== */}

          <div
            className={
              status.detected
                ? 'live-status danger'
                : 'live-status'
            }
          >

            <div className="status-symbol">

              {
                status.detected
                  ? <AlertTriangle/>
                  : <ShieldCheck/>
              }

            </div>


            <div>

              <span>
                DETECTION STATUS
              </span>


              <h2>

                {
                  status.detected
                    ? 'Potential accident'
                    : 'Road looks clear'
                }

              </h2>


              <p>

                {
                  status.detected
                    ? 'The AI detected person/vehicle overlap.'
                    : 'Monitoring camera frames continuously.'
                }

              </p>


              {status.severity && (

                <Severity
                  severity={
                    status.severity
                  }
                />

              )}

            </div>

          </div>


          {/* =================================================
              LIVE CONTROLS
          ================================================== */}

          <div
            className="card"
            style={{
              padding: 18
            }}
          >

            <div className="card-label">
              LIVE CONTROLS
            </div>


            <button
              className={
                active
                  ? 'danger-btn big'
                  : 'primary-btn big'
              }
              onClick={
                active
                  ? stop
                  : start
              }
              disabled={
                !active &&
                (
                  !socketReady ||
                  (
                    user?.user_type ===
                      'hospital' &&
                    !cameraId
                  )
                )
              }
              style={{
                width: '100%',
                marginTop: 14,
                justifyContent:
                  'center'
              }}
            >

              {active ? (

                <>
                  <X size={18}/>
                  Stop live detection
                </>

              ) : (

                <>
                  <Radio size={18}/>
                  Start live detection
                </>

              )}

            </button>

          </div>


          {/* =================================================
              CAMERA INFO
          ================================================== */}

          <div
            className="card"
            style={{
              padding: 18
            }}
          >

            <div className="card-label">
              CAMERA INFO
            </div>


            <div
              style={{
                display: 'flex',
                flexDirection:
                  'column',
                gap: 15,
                marginTop: 16
              }}
            >

              <div
                style={{
                  display: 'flex',
                  justifyContent:
                    'space-between',
                  gap: 20
                }}
              >

                <span
                  style={{
                    color:
                      '#8d99ac'
                  }}
                >
                  Camera
                </span>


                <strong
                  style={{
                    textAlign:
                      'right',
                    color:
                      '#dbe4f4'
                  }}
                >

                  {
                    selectedCamera?.name ||
                    (
                      user?.user_type ===
                      'hospital'
                        ? 'Not selected'
                        : 'Browser camera'
                    )
                  }

                </strong>

              </div>


              <div
                style={{
                  display: 'flex',
                  justifyContent:
                    'space-between',
                  gap: 20
                }}
              >

                <span
                  style={{
                    color:
                      '#8d99ac'
                  }}
                >
                  Status
                </span>


                <strong
                  style={{
                    color:
                      active
                        ? '#43e6a5'
                        : '#ff5264'
                  }}
                >

                  <span
                    style={{
                      display:
                        'inline-block',
                      width: 7,
                      height: 7,
                      borderRadius:
                        '50%',
                      background:
                        active
                          ? '#43e6a5'
                          : '#ff5264',
                      marginRight: 7
                    }}
                  />

                  {
                    active
                      ? 'Online'
                      : 'Offline'
                  }

                </strong>

              </div>


              <div
                style={{
                  display: 'flex',
                  justifyContent:
                    'space-between',
                  gap: 20
                }}
              >

                <span
                  style={{
                    color:
                      '#8d99ac'
                  }}
                >
                  Resolution
                </span>


                <strong
                  style={{
                    color:
                      '#dbe4f4'
                  }}
                >

                  {
                    active &&
                    video.current?.videoWidth

                      ? `${video.current.videoWidth} × ${video.current.videoHeight}`

                      : '—'
                  }

                </strong>

              </div>


              <div
                style={{
                  display: 'flex',
                  justifyContent:
                    'space-between',
                  gap: 20
                }}
              >

                <span
                  style={{
                    color:
                      '#8d99ac'
                  }}
                >
                  GPS
                </span>


                <strong
                  style={{
                    color:
                      '#dbe4f4'
                  }}
                >

                  {
                    gps
                      ? 'Linked'
                      : 'Not linked'
                  }

                </strong>

              </div>

            </div>

          </div>

        </div>

      </div>

    </div>
  );
}


/* =========================================================
   CAMERAS PAGE
========================================================= */

function CamerasPage({
  notify
}) {

  const [rows, setRows] =
    useState([]);


  const [form, setForm] =
    useState({
      name: '',
      location: ''
    });


  const [loading, setLoading] =
    useState(true);


  const [saving, setSaving] =
    useState(false);


  const load = async () => {

    setLoading(true);


    try {

      const data =
        await api(
          '/api/cameras/my'
        );


      setRows(
        Array.isArray(data)
          ? data
          : []
      );

    } catch (error) {

      setRows([]);


      notify(
        'error',
        `Could not load cameras: ${error.message}`
      );

    } finally {

      setLoading(false);

    }

  };


  useEffect(() => {

    load();

  }, []);


  const add = async () => {

    if (!form.name.trim()) {

      notify(
        'error',
        'Enter a camera name.'
      );

      return;

    }


    setSaving(true);


    try {

      await api(
        '/api/cameras/request',
        {
          method: 'POST',
          body: JSON.stringify({
            name:
              form.name.trim(),
            location:
              form.location.trim()
          })
        }
      );


      setForm({
        name: '',
        location: ''
      });


      await load();


      notify(
        'success',
        'Camera added successfully.'
      );

    } catch (error) {

      notify(
        'error',
        `Could not add camera: ${error.message}`
      );

    } finally {

      setSaving(false);

    }

  };


  return (
    <div className="page narrow">

      <div className="section-head">

        <div>

          <div className="eyebrow">

            <Camera size={14}/>

            CAMERA NETWORK

          </div>


          <h1>
            CCTV sources
          </h1>


          <p>
            Register cameras that
            can feed accident analysis.
          </p>

        </div>


        <button
          className="ghost-btn"
          onClick={load}
          disabled={loading}
        >

          <Activity size={15}/>

          Refresh

        </button>

      </div>


      <div className="split">

        {/* ADD CAMERA */}

        <div className="card">

          <h3>
            Add camera
          </h3>


          <p
            style={{
              color: '#8d99ac',
              fontSize: 13
            }}
          >
            Create a source for live
            detection and video analysis.
          </p>


          <input
            placeholder="Camera name"
            value={form.name}
            onChange={e =>
              setForm({
                ...form,
                name:
                  e.target.value
              })
            }
          />


          <input
            placeholder="Location"
            value={form.location}
            onChange={e =>
              setForm({
                ...form,
                location:
                  e.target.value
              })
            }
          />


          <button
            className="primary-btn"
            onClick={add}
            disabled={saving}
          >

            {saving ? (

              <>
                <span className="spinner"/>
                Adding…
              </>

            ) : (

              <>
                <Camera size={16}/>
                Add camera
              </>

            )}

          </button>

        </div>


        {/* REGISTERED CAMERAS */}

        <div className="card">

          <h3>

            Registered cameras

            <span className="count">
              {rows.length}
            </span>

          </h3>


          {loading ? (

            <div className="empty">

              <span className="spinner"/>

              <strong>
                Loading cameras…
              </strong>

              <span>
                Checking the FastAPI service.
              </span>

            </div>

          ) : rows.length ? (

            rows.map(camera => (

              <div
                className="list-row"
                key={camera.id}
              >

                <div className="row-icon">

                  <Camera size={16}/>

                </div>


                <div>

                  <strong>

                    {
                      camera.name ||
                      'Unnamed camera'
                    }

                  </strong>


                  <small>

                    {
                      camera.location ||
                      'Location not set'
                    }

                  </small>

                </div>


                <StatusPill
                  value={
                    camera.status ||
                    'pending'
                  }
                />

              </div>

            ))

          ) : (

            <EmptyState
              icon={Camera}
              title="No cameras yet"
              text="Add your first CCTV source using the form."
            />

          )}

        </div>

      </div>


      <div
        className="card"
        style={{
          marginTop: 14
        }}
      >

        <div className="card-label">
          TROUBLESHOOTING
        </div>


        <p
          style={{
            margin: '10px 0 0',
            color: '#8d99ac',
            lineHeight: 1.7,
            fontSize: 13
          }}
        >

          If this page shows an
          API/database error, open
          <strong
            style={{
              color: '#dbe4f4'
            }}
          >
            {' '}http://localhost:8000/docs
          </strong>
          {' '}
          and verify that the FastAPI
          server and MySQL database
          are running.

        </p>

      </div>

    </div>
  );
}


/* =========================================================
   ALERTS PAGE
========================================================= */

function AlertsPage({
  incoming,
  setIncoming,
  notify
}) {

  const [rows, setRows] =
    useState([]);


  const [loading, setLoading] =
    useState(true);


  const load = async () => {

    setLoading(true);


    try {

      const data =
        await api(
          '/api/alerts'
        );


      setRows(
        Array.isArray(data)
          ? data
          : []
      );

    } catch (error) {

      notify(
        'error',
        error.message
      );

    } finally {

      setLoading(false);

    }

  };


  useEffect(() => {

    load();

  }, []);


  return (
    <div className="page narrow">

      <div className="section-head">

        <div>

          <div className="eyebrow">

            <AlertTriangle size={14}/>

            INCIDENT LOG

          </div>


          <h1>
            Recent alerts
          </h1>


          <p>
            Confirmed accident events
            and emergency reports.
          </p>

        </div>


        <div
          style={{
            display: 'flex',
            gap: 10
          }}
        >

          {incoming && (

            <button
              className="ghost-btn"
              onClick={() =>
                setIncoming(null)
              }
            >

              Dismiss live alert

            </button>

          )}


          <button
            className="ghost-btn"
            onClick={load}
            disabled={loading}
          >

            <Activity size={15}/>

            Refresh

          </button>

        </div>

      </div>


      {loading ? (

        <div className="card">

          <EmptyState
            icon={Activity}
            title="Loading alerts…"
            text="Checking the FastAPI service for recent incidents."
          />

        </div>

      ) : rows.length ? (

        <div>

          {rows.map(alert => (

            <AlertRow
              key={alert.id}
              alert={alert}
            />

          ))}

        </div>

      ) : (

        <div className="card">

          <EmptyState
            icon={CheckCircle2}
            title="No alerts recorded"
            text="Confirmed events will appear here."
          />

        </div>

      )}

    </div>
  );
}


/* =========================================================
   ALERT ROW
========================================================= */

function AlertRow({
  alert
}) {

  const screenshot =
    alert.screenshot_path
      ? mediaUrl(
          `/media/screenshots/${alert.screenshot_path
            .split(/[\\/]/)
            .pop()}`
        )
      : null;


  return (
    <div
      className={
        alert.accident_detected
          ? 'alert-row accident'
          : 'alert-row'
      }
    >

      <div className="alert-main">

        <div className="alert-symbol">

          <AlertTriangle/>

        </div>


        <div>

          <div className="alert-top">

            <strong>

              {
                alert.video_name ||
                'Incident'
              }

            </strong>


            {alert.severity_label && (

              <Severity
                severity={{
                  label:
                    alert.severity_label,
                  score:
                    alert.severity_score
                }}
              />

            )}

          </div>


          <p>

            {
              alert.camera_name ||
              'Camera source'
            }

            {' · '}

            {alert.created_at}

          </p>


          <span>

            <MapPin size={13}/>

            {
              alert.location ||
              'Location unavailable'
            }

          </span>

        </div>

      </div>


      <div className="alert-media">

        {screenshot && (

          <img
            src={screenshot}
            alt="Accident evidence"
          />

        )}


        <div>

          {
            alert.email_sent
              ? (
                <span className="success-tag">

                  <CheckCircle2 size={13}/>

                  Email sent

                </span>
              )
              : (
                <span className="muted-tag">

                  Email not sent

                </span>
              )
          }

        </div>

      </div>

    </div>
  );
}


/* =========================================================
   ANALYTICS PAGE
========================================================= */

function AnalyticsPage() {

  const [data, setData] =
    useState(null);


  const [loading, setLoading] =
    useState(true);


  const load = async () => {

    setLoading(true);


    try {

      const result =
        await api(
          '/api/stats'
        );


      setData(result);

    } catch {

      setData(null);

    } finally {

      setLoading(false);

    }

  };


  useEffect(() => {

    load();

  }, []);


  const days =
    data?.per_day || [];


  const severity =
    data?.severity_breakdown || [];


  const pie =
    severity.map(item => ({
      name:
        item.severity_label ||
        'Unknown',
      value:
        Number(item.count)
    }));


  return (
    <div className="page">

      <div className="section-head">

        <div>

          <div className="eyebrow">

            <BarChart3 size={14}/>

            OPERATIONAL ANALYTICS

          </div>


          <h1>
            Response intelligence
          </h1>


          <p>
            30-day incident trends
            and severity distribution.
          </p>

        </div>


        <button
          className="ghost-btn"
          onClick={load}
          disabled={loading}
        >

          <Activity size={15}/>

          Refresh

        </button>

      </div>


      <div className="analytics-metrics">

        {[
          [
            'Videos',
            data?.summary
              ?.total_videos || 0
          ],
          [
            'Accidents',
            data?.summary
              ?.total_accidents || 0
          ],
          [
            'Emails sent',
            data?.summary
              ?.emails_sent || 0
          ]
        ].map(
          ([label, value]) => (

            <div
              className="analytics-metric"
              key={label}
            >

              <span>
                {label}
              </span>

              <strong>
                {value}
              </strong>

            </div>

          )
        )}

      </div>


      <div className="charts">

        {/* ACCIDENT TREND */}

        <div className="card chart-card">

          <h3>
            Accidents · last 30 days
          </h3>


          <div className="chart">

            <ResponsiveContainer
              width="100%"
              height="100%"
            >

              <AreaChart
                data={days}
              >

                <CartesianGrid
                  strokeDasharray="3 3"
                />


                <XAxis
                  dataKey="day"
                  tick={{
                    fontSize: 11
                  }}
                />


                <YAxis
                  allowDecimals={false}
                />


                <Tooltip/>


                <Area
                  type="monotone"
                  dataKey="count"
                  fillOpacity={0.16}
                  strokeWidth={2}
                />

              </AreaChart>

            </ResponsiveContainer>

          </div>

        </div>


        {/* SEVERITY */}

        <div className="card chart-card">

          <h3>
            Severity mix
          </h3>


          <div className="chart">

            {pie.length ? (

              <ResponsiveContainer
                width="100%"
                height="100%"
              >

                <PieChart>

                  <Pie
                    data={pie}
                    dataKey="value"
                    nameKey="name"
                    cx="50%"
                    cy="50%"
                    outerRadius={90}
                    label
                  >

                    {pie.map(
                      (_, index) => (

                        <Cell
                          key={index}
                        />

                      )
                    )}

                  </Pie>


                  <Legend/>


                  <Tooltip/>

                </PieChart>

              </ResponsiveContainer>

            ) : (

              <EmptyState
                icon={BarChart3}
                title={
                  loading
                    ? 'Loading analytics…'
                    : 'No severity data'
                }
                text={
                  loading
                    ? 'Fetching operational statistics.'
                    : 'Severity information will appear after incidents are recorded.'
                }
              />

            )}

          </div>

        </div>

      </div>

    </div>
  );
}


/* =========================================================
   RESULT CARD
========================================================= */

function ResultCard({
  data,
  title
}) {

  return (
    <div className="result-card">

      <CheckCircle2/>


      <div>

        <h3>
          {title}
        </h3>


        <p>
          {data.message}
        </p>


        {
          data.nearest_hospitals
            ?.length > 0 && (

            <div className="hospital-chips">

              {
                data.nearest_hospitals.map(
                  hospital => (

                    <span
                      key={hospital.id}
                    >

                      <Hospital size={13}/>

                      {hospital.name}

                      {' · '}

                      {hospital.distance_km}
                      {' km'}

                    </span>

                  )
                )
              }

            </div>

          )
        }

      </div>

    </div>
  );
}


/* =========================================================
   INCOMING ALERT
========================================================= */

function IncomingAlert({
  data,
  close
}) {

  return (
    <div className="incoming">

      <div className="incoming-icon">

        <Siren/>

      </div>


      <div>

        <span>
          URGENT INCIDENT
        </span>


        <h3>

          {
            data.sos
              ? 'SOS emergency'
              : 'Accident detected'
          }

        </h3>


        <p>
          {
            data.location ||
            'Location unavailable'
          }
        </p>


        {data.severity && (

          <Severity
            severity={data.severity}
          />

        )}

      </div>


      <button onClick={close}>

        <X/>

      </button>

    </div>
  );
}


/* =========================================================
   SEVERITY
========================================================= */

function Severity({
  severity
}) {

  if (!severity) {
    return null;
  }


  return (
    <span
      className={
        `severity ${
          severity.label
            ?.toLowerCase() || ''
        }`
      }
    >

      <AlertTriangle size={12}/>

      {severity.label}

      {
        severity.score != null
          ? ` · ${severity.score}`
          : ''
      }

    </span>
  );
}


/* =========================================================
   STATUS PILL
========================================================= */

function StatusPill({
  value
}) {

  return (
    <span
      className={
        `status-pill ${value}`
      }
    >

      {value}

    </span>
  );
}


/* =========================================================
   EMPTY STATE
========================================================= */

function EmptyState({
  icon: Icon,
  title,
  text
}) {

  return (
    <div className="empty">

      <Icon/>

      <strong>
        {title}
      </strong>

      <span>
        {text}
      </span>

    </div>
  );
}


/* =========================================================
   NOTICE
========================================================= */

function Notice({
  notice
}) {

  return (
    <div
      className={
        `notice ${notice.type}`
      }
    >

      <span>

        {
          notice.type === 'error'
            ? <AlertTriangle size={16}/>
            : <CheckCircle2 size={16}/>
        }

      </span>


      {notice.text}

    </div>
  );
}