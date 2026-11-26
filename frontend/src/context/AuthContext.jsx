import React, { createContext, useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { authService } from '../services/authService'

const AuthContext = createContext(null)

export const AuthProvider = ({ children }) => {
  const navigate = useNavigate()
  const [user, setUser] = useState(null)
  const [token, setToken] = useState(() => localStorage.getItem('access_token'))
  const [isLoading, setIsLoading] = useState(true)

  const isAuthenticated = !!token && !!user

  const refreshUser = useCallback(async () => {
    try {
      const userData = await authService.getMe()
      setUser(userData)
      localStorage.setItem('user', JSON.stringify(userData))
    } catch {
      setToken(null)
      setUser(null)
      localStorage.removeItem('access_token')
      localStorage.removeItem('user')
    }
  }, [])

  useEffect(() => {
    const initAuth = async () => {
      const storedToken = localStorage.getItem('access_token')
      if (storedToken) {
        setToken(storedToken)
        await refreshUser()
      }
      setIsLoading(false)
    }
    initAuth()
  }, [refreshUser])

  const login = async (email, password) => {
    const data = await authService.login(email, password)
    const accessToken = data.access_token
    if (!accessToken) throw new Error('The server did not return an access token.')
    setToken(accessToken)
    localStorage.setItem('access_token', accessToken)
    try {
      const userData = await authService.getMe()
      setUser(userData)
      localStorage.setItem('user', JSON.stringify(userData))
      return userData
    } catch (error) {
      setToken(null)
      setUser(null)
      localStorage.removeItem('access_token')
      localStorage.removeItem('user')
      throw error
    }
  }

  const logout = () => {
    setToken(null)
    setUser(null)
    localStorage.removeItem('access_token')
    localStorage.removeItem('user')
    navigate('/login', { replace: true })
  }

  const register = async (data) => {
    const result = await authService.register(data)
    return result
  }

  return (
    <AuthContext.Provider
      value={{ user, token, isLoading, isAuthenticated, login, logout, register, refreshUser }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export default AuthContext
