import React, { useState, useEffect } from 'react';
import { View, Text, Button, StyleSheet, ActivityIndicator } from 'react-native';
import * as Google from 'expo-auth-session/providers/google';
import * as WebBrowser from 'expo-web-browser';
import { setGoogleToken, clearAuth, api } from './api';

WebBrowser.maybeCompleteAuthSession();

const GOOGLE_CLIENT_ID = process.env.EXPO_PUBLIC_GOOGLE_CLIENT_ID;

export default function App() {
  const [user, setUser]       = useState(null);
  const [data, setData]       = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState(null);

  const [request, response, promptAsync] = Google.useAuthRequest({
    clientId: GOOGLE_CLIENT_ID,
    scopes: ['openid', 'email', 'profile'],
  });

  useEffect(() => {
    if (response?.type === 'success' && response.authentication?.idToken) {
      const token = response.authentication.idToken;
      setGoogleToken(token);
      setUser(token);
      loadData();
    }
  }, [response]);

  async function loadData() {
    setLoading(true);
    setError(null);
    try {
      const result = await api.get();
      setData(result);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  function handleSignOut() {
    clearAuth();
    setUser(null);
    setData(null);
  }

  if (!user) {
    return (
      <View style={styles.center}>
        <Text style={styles.title}>App Template</Text>
        <Button title="Sign in with Google" onPress={() => promptAsync()} disabled={!request} />
        {error && <Text style={styles.error}>{error}</Text>}
      </View>
    );
  }

  if (loading) {
    return <View style={styles.center}><ActivityIndicator size="large" /></View>;
  }

  return (
    <View style={styles.container}>
      <Text style={styles.subtitle}>Signed in as {data?._user}</Text>
      {/* ── Your app UI goes here ── */}
      <Text style={styles.placeholder}>Replace this with your app content</Text>
      {error && <Text style={styles.error}>{error}</Text>}
      <Button title="Sign Out" onPress={handleSignOut} />
    </View>
  );
}

const styles = StyleSheet.create({
  center:      { flex: 1, justifyContent: 'center', alignItems: 'center', padding: 24 },
  container:   { flex: 1, padding: 24, paddingTop: 60 },
  title:       { fontSize: 28, fontWeight: 'bold', marginBottom: 24 },
  subtitle:    { fontSize: 14, color: '#666', marginBottom: 20 },
  placeholder: { fontSize: 16, color: '#999', marginVertical: 20, textAlign: 'center' },
  error:       { color: 'red', marginTop: 12, textAlign: 'center' },
});
